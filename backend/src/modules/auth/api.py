import datetime
import httpx
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.core.dependencies import (
    get_db,
    get_redis_client,
    get_authenticated_user_context,
    PermissionRequired
)
from src.core.logging import logger
from src.modules.auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordConfirm,
    SignupResponse,
    ProfileResponse,
    ProfileUpdate,
    ChangePasswordRequest,
    ChangeEmailRequest,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionResponse
)
from src.modules.auth.services import AuthService, RBACService

router = APIRouter(prefix="/auth", tags=["Authentication & Profiles"])


async def enforce_rate_limit(request: Request, redis_client: Any, endpoint_name: str, max_requests: int = 5, window_seconds: int = 60):
    """
    Redis-backed sliding window rate limiter for login/signup attempt protection.
    """
    if not redis_client:
        return
    
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:{endpoint_name}:{client_ip}"
    
    current = await redis_client.get(key)
    if current and int(current) >= max_requests:
        logger.warn("Rate limit breached for auth endpoint", endpoint=endpoint_name, ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later."
        )
    
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.incr(key)
        await pipe.expire(key, window_seconds)
        await pipe.execute()


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    schema: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis_client)
):
    await enforce_rate_limit(request, redis, "signup", max_requests=3, window_seconds=60)
    try:
        ip_addr = request.client.host if request.client else None
        user = await AuthService.create_user(db, schema, ip_addr)
        token = await AuthService.generate_email_verification(db, user.id)
        logger.info("Verification email simulated", email=user.email, token=token)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    schema: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis_client)
):
    await enforce_rate_limit(request, redis, "login", max_requests=5, window_seconds=60)
    ip_addr = request.client.host if request.client else None
    user = await AuthService.authenticate_user(db, schema.email, schema.password, ip_addr)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token, refresh_token = await AuthService.create_user_session(db, user)

    secure_cookie = settings.ENV == "production"
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="strict",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth/refresh"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=Dict[str, str], status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    old_token = request.cookies.get("refresh_token")
    if not old_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session refresh token cookie."
        )

    try:
        ip_addr = request.client.host if request.client else None
        access_token, new_refresh_token = await AuthService.rotate_session_token(db, old_token, ip_addr)
        
        secure_cookie = settings.ENV == "production"
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="strict",
            max_age=7 * 24 * 3600,
            path="/api/v1/auth/refresh"
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("refresh_token")
    if token:
        ip_addr = request.client.host if request.client else None
        await AuthService.revoke_user_session(db, token, ip_addr)
        
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh"
    )
    return {"message": "Logged out successfully."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    schema: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    token = await AuthService.generate_password_reset(db, schema.email)
    if token:
        logger.info("Password reset token simulated email", email=schema.email, token=token)
    return {"message": "If the email is registered, a password reset link has been triggered."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: Request,
    schema: ResetPasswordConfirm,
    db: AsyncSession = Depends(get_db)
):
    ip_addr = request.client.host if request.client else None
    success = await AuthService.reset_password(db, schema.token, schema.new_password, ip_addr)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")
    return {"message": "Password updated successfully."}


@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: Request,
    token: str = Query(..., description="Email verification token value"),
    db: AsyncSession = Depends(get_db)
):
    ip_addr = request.client.host if request.client else None
    success = await AuthService.verify_email_token(db, token, ip_addr)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired email verification token.")
    return {"message": "Email verified successfully."}


@router.get("/google")
async def google_login():
    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return Response(headers={"Location": authorization_url}, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    request: Request,
    code: str = Query(...),
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed Google token exchange.")
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed user profile lookup.")
            
        user_data = userinfo_response.json()
        email = user_data.get("email")
        first_name = user_data.get("given_name", "Google")
        last_name = user_data.get("family_name", "User")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google account email not shared.")
            
        ip_addr = request.client.host if request.client else None
        user = await AuthService.authenticate_google_user(db, email, first_name, last_name, ip_addr)
        access_token, refresh_token = await AuthService.create_user_session(db, user)
        
        secure_cookie = settings.ENV == "production"
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="strict",
            max_age=7 * 24 * 3600,
            path="/api/v1/auth/refresh"
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }


# --- Phase 2C: Profile APIs ---

@router.get("/profile", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the complete profile data of the logged-in user.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    from src.modules.auth.models import User
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return user


@router.put("/profile", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    schema: ProfileUpdate,
    request: Request,
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the logged-in user profile attributes, logging audit traces.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    user = await AuthService.update_profile(db, user_id, schema, ip_addr)
    return user


@router.post("/profile/avatar", status_code=status.HTTP_200_OK)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(..., description="Avatar image file payload"),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads user profile avatars to S3 bucket (MinIO) and sets avatar_url.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    file_content = await file.read()
    ip_addr = request.client.host if request.client else None
    try:
        avatar_url = await AuthService.upload_avatar(
            db=db,
            user_id=user_id,
            file_content=file_content,
            content_type=file.content_type,
            file_size=len(file_content),
            filename=file.filename,
            request_ip=ip_addr
        )
        return {"avatar_url": avatar_url}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/profile/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    schema: ChangePasswordRequest,
    request: Request,
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates user credentials, verifying current passwords first.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    success = await AuthService.change_password(db, user_id, schema, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password verification failed.")
    return {"message": "Password changed successfully."}


@router.post("/profile/change-email", status_code=status.HTTP_200_OK)
async def change_email(
    schema: ChangeEmailRequest,
    request: Request,
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Changes user's registered email address, sending a verify link simulation.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    try:
        user, token = await AuthService.change_email(db, user_id, schema, ip_addr)
        logger.info("Verification code triggered for new email", email=user.email, token=token)
        return {"message": "Email updated successfully. Please verify your new address."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/profile/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request: Request,
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers a resend of verification links for unverified profiles.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    # Query user details
    from src.modules.auth.models import User
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one()
    
    if user.is_verified:
        return {"message": "Email address is already verified."}

    token = await AuthService.generate_email_verification(db, user_id)
    await AuditLogService.log_event(
        db, user_id=user_id, org_id=user.organization_id, workspace_id=None, action="RESEND_VERIFICATION", ip_address=ip_addr
    )
    logger.info("Resend verification code simulated", email=user.email, token=token)
    return {"message": "Verification link has been sent."}


# --- Phase 2C: RBAC Roles & Permissions ---

@router.get("/roles", response_model=List[RoleResponse], dependencies=[Depends(PermissionRequired("roles:read"))])
async def list_roles(db: AsyncSession = Depends(get_db)):
    """
    Lists all configured roles and permissions. (Requires 'roles:read')
    """
    return await RBACService.list_roles(db)


@router.get("/permissions", response_model=List[PermissionResponse], dependencies=[Depends(PermissionRequired("permissions:read"))])
async def list_permissions(db: AsyncSession = Depends(get_db)):
    """
    Lists all available system permissions. (Requires 'permissions:read')
    """
    return await RBACService.list_permissions(db)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("roles:write"))])
async def create_role(
    schema: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a custom workspace/organization role. (Requires 'roles:write')
    """
    try:
        ip_addr = request.client.host if request.client else None
        return await RBACService.create_role(db, schema, ip_addr)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/roles/{id}", response_model=RoleResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("roles:write"))])
async def update_role(
    id: uuid.UUID,
    schema: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates custom role settings or permissions list. (Requires 'roles:write')
    """
    ip_addr = request.client.host if request.client else None
    role = await RBACService.update_role(db, id, schema, ip_addr)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return role


@router.delete("/roles/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("roles:write"))])
async def delete_role(
    id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Removes a custom workspace or organization role. (Requires 'roles:write')
    """
    ip_addr = request.client.host if request.client else None
    success = await RBACService.delete_role(db, id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return {"message": "Role deleted successfully."}
