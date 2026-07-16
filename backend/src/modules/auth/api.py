import datetime
import httpx
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.core.dependencies import get_db, get_redis_client, get_authenticated_user_context
from src.core.logging import logger
from src.modules.auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordConfirm,
    SignupResponse
)
from src.modules.auth.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def enforce_rate_limit(request: Request, redis_client: Any, endpoint_name: str, max_requests: int = 5, window_seconds: int = 60):
    """
    Redis-backed sliding window rate limiter for login/signup attempt protection.
    """
    if not redis_client:
        return  # Gracefully proceed if Redis cache is offline
    
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:{endpoint_name}:{client_ip}"
    
    current = await redis_client.get(key)
    if current and int(current) >= max_requests:
        logger.warn("Rate limit breached for auth endpoint", endpoint=endpoint_name, ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later."
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
        user = await AuthService.create_user(db, schema)
        # Dynamic Token trigger (logging simulation)
        token = await AuthService.generate_email_verification(db, user.id)
        logger.info("Verification email simulation triggered", email=user.email, token=token)
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
    user = await AuthService.authenticate_user(db, schema.email, schema.password)
    if not user:
        logger.warn("Login audit: Failed credentials login attempt", email=schema.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token, refresh_token = await AuthService.create_user_session(db, user)

    # Secure HTTPOnly Cookie configuration
    secure_cookie = settings.ENV == "production"
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="strict",
        max_age=7 * 24 * 3600,  # 7 days
        path="/api/v1/auth/refresh"
    )

    logger.info("Login audit: User logged in successfully", user_id=str(user.id), email=user.email)
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
        logger.warn("Token refresh failed: cookie refresh_token not present.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session refresh token cookie."
        )

    try:
        access_token, new_refresh_token = await AuthService.rotate_session_token(db, old_token)
        
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
        logger.info("Token refresh: session token rotated successfully.")
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
        await AuthService.revoke_user_session(db, token)
        
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh"
    )
    logger.info("Logout audit: User logged out session successfully.")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    user_id = user_context.get("sub")
    from src.modules.auth.models import User
    from sqlalchemy import select
    
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
         raise HTTPException(status_code=404, detail="User profile not found.")
    return user


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    schema: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    token = await AuthService.generate_password_reset(db, schema.email)
    if token:
        logger.info("Password reset token simulated email", email=schema.email, token=token)
    # Always return 200 OK to prevent email enumeration attacks
    return {"message": "If the email is registered, a password reset link has been triggered."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    schema: ResetPasswordConfirm,
    db: AsyncSession = Depends(get_db)
):
    success = await AuthService.reset_password(db, schema.token, schema.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")
    return {"message": "Password updated successfully."}


@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    token: str = Query(..., description="Email verification token value"),
    db: AsyncSession = Depends(get_db)
):
    success = await AuthService.verify_email_token(db, token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired email verification token.")
    return {"message": "Email verified successfully."}


@router.get("/google")
async def google_login():
    """
    Redirects client to Google OAuth Consent Screen.
    """
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
    code: str = Query(..., description="Google OAuth authorization code"),
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Google OAuth token exchange callback. Links account by email or creates user on first login.
    """
    # Exchange Auth Code for ID Token
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
            logger.error("Google OAuth token exchange failed", body=token_response.text)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed Google token exchange.")
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get User details from google userinfo API
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_response.status_code != 200:
            logger.error("Failed to query google userinfo", body=userinfo_response.text)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed user profile lookup.")
            
        user_data = userinfo_response.json()
        email = user_data.get("email")
        first_name = user_data.get("given_name", "Google")
        last_name = user_data.get("family_name", "User")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google account email not shared.")
            
        # Authenticate and link/register the user
        user = await AuthService.authenticate_google_user(db, email, first_name, last_name)
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
        
        logger.info("Google OAuth login session completed", user_id=str(user.id), email=email)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
