import datetime
import io
import uuid
import secrets
from typing import Optional, Tuple, List
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from src.core.logging import logger
from src.core.storage import storage_manager
from src.config import settings
from src.modules.auth.models import (
    User,
    RefreshToken,
    EmailVerificationToken,
    PasswordResetToken,
    Role,
    Permission,
    AuditLog
)
from src.modules.auth.schemas import UserCreate, ProfileUpdate, ChangePasswordRequest, ChangeEmailRequest, RoleCreate, RoleUpdate


class AuditLogService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        user_id: Optional[uuid.UUID],
        org_id: Optional[uuid.UUID],
        workspace_id: Optional[uuid.UUID],
        action: str,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Registers a new security audit log in the database.
        """
        audit = AuditLog(
            user_id=user_id,
            organization_id=org_id,
            workspace_id=workspace_id,
            action=action,
            ip_address=ip_address
        )
        db.add(audit)
        await db.commit()
        logger.info("Security audit logged", action=action, user_id=str(user_id) if user_id else None)
        return audit


class AuthService:
    @staticmethod
    async def create_user(db: AsyncSession, schema: UserCreate, request_ip: Optional[str] = None) -> User:
        """
        Creates a new user profile with hashed credentials.
        """
        query = select(User).where(User.email == schema.email)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            logger.warn("Signup failed. Email already registered.", email=schema.email)
            raise ValueError("Email already registered.")

        password_hash = get_password_hash(schema.password)
        user = User(
            email=schema.email,
            password_hash=password_hash,
            first_name=schema.first_name,
            last_name=schema.last_name,
            org_role="ORG_MEMBER",
            is_active=True,
            is_verified=False
        )
        db.add(user)
        await db.flush()  # Extract ID
        
        # Log Audit Log
        await AuditLogService.log_event(
            db, user_id=user.id, org_id=None, workspace_id=None, action="USER_SIGNUP", ip_address=request_ip
        )
        
        await db.commit()
        await db.refresh(user)
        logger.info("User registered successfully", user_id=str(user.id), email=user.email)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, plain_password: str, request_ip: Optional[str] = None) -> Optional[User]:
        """
        Authenticates credentials against stored password hashes.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warn("Authentication failed. User not found.", email=email)
            await AuditLogService.log_event(
                db, user_id=None, org_id=None, workspace_id=None, action="LOGIN_FAILED_USER_NOT_FOUND", ip_address=request_ip
            )
            return None

        if not verify_password(plain_password, user.password_hash):
            logger.warn("Authentication failed. Password mismatch.", email=email)
            await AuditLogService.log_event(
                db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="LOGIN_FAILED_PASSWORD_MISMATCH", ip_address=request_ip
            )
            return None

        if not user.is_active:
            logger.warn("Authentication failed. Account inactive.", email=email)
            return None

        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="LOGIN_SUCCESS", ip_address=request_ip
        )
        logger.info("User authenticated successfully", user_id=str(user.id), email=email)
        return user

    @staticmethod
    async def create_user_session(db: AsyncSession, user: User) -> Tuple[str, str]:
        """
        Generates access and refresh tokens, saving refresh token metadata to the database.
        """
        claims = {
            "sub": str(user.id),
            "email": user.email,
            "org_role": user.org_role,
            "org_id": str(user.organization_id) if user.organization_id else None
        }
        access_token = create_access_token(claims)
        
        # Generate and save refresh token
        refresh_secret = secrets.token_hex(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        
        refresh_token_db = RefreshToken(
            user_id=user.id,
            token=refresh_secret,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(refresh_token_db)
        await db.commit()
        
        logger.info("New refresh token session saved", user_id=str(user.id))
        return access_token, refresh_secret

    @staticmethod
    async def rotate_session_token(db: AsyncSession, old_token: str, request_ip: Optional[str] = None) -> Tuple[str, str]:
        """
        Rotates an existing refresh token session, invalidating the old token and generating new access/refresh pairs.
        """
        query = select(RefreshToken).where(RefreshToken.token == old_token, RefreshToken.is_revoked == False)
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()

        if not token_record:
            logger.warn("Token rotation failed. Invalid or revoked token.")
            raise ValueError("Invalid refresh token session.")

        if token_record.expires_at < datetime.datetime.utcnow():
            logger.warn("Token rotation failed. Expired token session.")
            raise ValueError("Expired refresh token session.")

        # Revoke old token
        token_record.is_revoked = True
        await db.commit()

        # Query user details
        user_query = select(User).where(User.id == token_record.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()

        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="TOKEN_REFRESH", ip_address=request_ip
        )

        # Generate new session
        return await AuthService.create_user_session(db, user)

    @staticmethod
    async def revoke_user_session(db: AsyncSession, token: str, request_ip: Optional[str] = None) -> None:
        """
        Revokes a refresh token, signing the user out.
        """
        query = select(RefreshToken).where(RefreshToken.token == token)
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True
            await AuditLogService.log_event(
                db, user_id=token_record.user_id, org_id=None, workspace_id=None, action="LOGOUT", ip_address=request_ip
            )
            await db.commit()
            logger.info("User session revoked", user_id=str(token_record.user_id))

    @staticmethod
    async def generate_email_verification(db: AsyncSession, user_id: uuid.UUID) -> str:
        """
        Generates and stores a unique email verification token.
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        
        verification = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(verification)
        await db.commit()
        return token

    @staticmethod
    async def verify_email_token(db: AsyncSession, token: str, request_ip: Optional[str] = None) -> bool:
        """
        Verifies the token and marks the associated user email as verified.
        """
        query = select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        result = await db.execute(query)
        verification = result.scalar_one_or_none()
        
        if not verification:
            return False
            
        if verification.expires_at < datetime.datetime.utcnow():
            return False
            
        # Update user status
        user_query = select(User).where(User.id == verification.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()
        user.is_verified = True
        
        # Clean verification tokens
        await db.delete(verification)
        
        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="EMAIL_VERIFY_SUCCESS", ip_address=request_ip
        )
        await db.commit()
        logger.info("Email verified successfully", user_id=str(user.id))
        return True

    @staticmethod
    async def generate_password_reset(db: AsyncSession, email: str) -> Optional[str]:
        """
        Generates a password reset token if the email is registered.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
            
        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        
        reset = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset)
        await db.commit()
        return token

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str, request_ip: Optional[str] = None) -> bool:
        """
        Updates the password hash using the verification token.
        """
        query = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await db.execute(query)
        reset = result.scalar_one_or_none()
        
        if not reset or reset.expires_at < datetime.datetime.utcnow():
            return False
            
        user_query = select(User).where(User.id == reset.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()
        
        user.password_hash = get_password_hash(new_password)
        await db.delete(reset)
        
        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="PASSWORD_RESET_SUCCESS", ip_address=request_ip
        )
        await db.commit()
        logger.info("Password reset successfully", user_id=str(user.id))
        return True

    @staticmethod
    async def authenticate_google_user(db: AsyncSession, email: str, first_name: str, last_name: str, request_ip: Optional[str] = None) -> User:
        """
        OAuth linking flow. Logs in existing users by matching email, or creates a new user on first login.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.is_verified = True
            await AuditLogService.log_event(
                db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="GOOGLE_LOGIN_SUCCESS", ip_address=request_ip
            )
            await db.commit()
            logger.info("Google OAuth login match success", user_id=str(user.id), email=email)
            return user
            
        user = User(
            email=email,
            password_hash=get_password_hash(secrets.token_urlsafe(24)),
            first_name=first_name,
            last_name=last_name,
            org_role="ORG_MEMBER",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        await db.flush()
        
        await AuditLogService.log_event(
            db, user_id=user.id, org_id=None, workspace_id=None, action="GOOGLE_SIGNUP_SUCCESS", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(user)
        logger.info("First login google OAuth account created", user_id=str(user.id), email=email)
        return user

    # --- Profile & Settings Management ---

    @staticmethod
    async def update_profile(db: AsyncSession, user_id: uuid.UUID, schema: ProfileUpdate, request_ip: Optional[str] = None) -> User:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one()

        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="PROFILE_UPDATE", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def change_password(db: AsyncSession, user_id: uuid.UUID, schema: ChangePasswordRequest, request_ip: Optional[str] = None) -> bool:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one()

        if not verify_password(schema.current_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(schema.new_password)
        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="PASSWORD_CHANGE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def change_email(db: AsyncSession, user_id: uuid.UUID, schema: ChangeEmailRequest, request_ip: Optional[str] = None) -> Tuple[User, str]:
        # Validate unique email
        query = select(User).where(User.email == schema.new_email)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Email already in use.")

        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()

        user.email = schema.new_email
        user.is_verified = False

        token = await AuthService.generate_email_verification(db, user_id)
        
        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="EMAIL_CHANGE", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(user)
        return user, token

    @staticmethod
    async def upload_avatar(
        db: AsyncSession,
        user_id: uuid.UUID,
        file_content: bytes,
        content_type: str,
        file_size: int,
        filename: str,
        request_ip: Optional[str] = None
    ) -> str:
        """
        Validates and uploads profile avatar files to MinIO storage bucket, updating user records.
        """
        # Validate format
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if content_type not in allowed_types:
            raise ValueError("Unsupported format. Allowed formats: PNG, JPG, JPEG, WEBP.")

        # Limit size to 5MB
        if file_size > 5 * 1024 * 1024:
            raise ValueError("File size limit exceeded. Maximum allowed: 5MB.")

        # Upload to MinIO
        key = f"avatars/{user_id}/{filename}"
        storage_manager.client.put_object(
            settings.MINIO_BUCKET_NAME,
            key,
            io.BytesIO(file_content),
            length=file_size,
            content_type=content_type
        )

        avatar_url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{key}"

        # Update User
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one()
        user.avatar_url = avatar_url

        await AuditLogService.log_event(
            db, user_id=user.id, org_id=user.organization_id, workspace_id=None, action="AVATAR_UPLOAD", ip_address=request_ip
        )
        await db.commit()
        return avatar_url


class RBACService:
    @staticmethod
    async def create_role(db: AsyncSession, schema: RoleCreate, request_ip: Optional[str] = None) -> Role:
        """
        Creates a custom system or tenant role, mapping permission lists.
        """
        query = select(Role).where(Role.name == schema.name)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Role name already exists.")

        # Resolve permissions by name
        perm_query = select(Permission).where(Permission.name.in_(schema.permissions))
        perm_result = await db.execute(perm_query)
        permissions_list = list(perm_result.scalars().all())

        role = Role(
            name=schema.name,
            description=schema.description,
            role_type=schema.role_type,
            permissions=permissions_list
        )
        db.add(role)
        await db.flush()

        await AuditLogService.log_event(
            db, user_id=None, org_id=None, workspace_id=None, action=f"ROLE_CREATION:{schema.name}", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def update_role(db: AsyncSession, role_id: uuid.UUID, schema: RoleUpdate, request_ip: Optional[str] = None) -> Optional[Role]:
        query = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await db.execute(query)
        role = result.scalar_one_or_none()
        if not role:
            return None

        if schema.description is not None:
            role.description = schema.description

        if schema.permissions is not None:
            perm_query = select(Permission).where(Permission.name.in_(schema.permissions))
            perm_result = await db.execute(perm_query)
            role.permissions = list(perm_result.scalars().all())

        await AuditLogService.log_event(
            db, user_id=None, org_id=None, workspace_id=None, action=f"ROLE_UPDATE:{role.name}", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def delete_role(db: AsyncSession, role_id: uuid.UUID, request_ip: Optional[str] = None) -> bool:
        query = select(Role).where(Role.id == role_id)
        result = await db.execute(query)
        role = result.scalar_one_or_none()
        if not role:
            return False

        await db.delete(role)
        await AuditLogService.log_event(
            db, user_id=None, org_id=None, workspace_id=None, action=f"ROLE_DELETION:{role.name}", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def get_role(db: AsyncSession, role_id: uuid.UUID) -> Optional[Role]:
        query = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_roles(db: AsyncSession) -> List[Role]:
        query = select(Role).options(selectinload(Role.permissions))
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def list_permissions(db: AsyncSession) -> List[Permission]:
        query = select(Permission)
        result = await db.execute(query)
        return list(result.scalars().all())
