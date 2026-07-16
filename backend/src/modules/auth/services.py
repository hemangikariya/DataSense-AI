import datetime
import uuid
import secrets
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from src.core.logging import logger
from src.modules.auth.models import User, RefreshToken, EmailVerificationToken, PasswordResetToken
from src.modules.auth.schemas import UserCreate


class AuthService:
    @staticmethod
    async def create_user(db: AsyncSession, schema: UserCreate) -> User:
        """
        Creates a new user profile with hashed credentials.
        """
        # Validate unique email
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
        await db.commit()
        await db.refresh(user)
        logger.info("User registered successfully", user_id=str(user.id), email=user.email)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, plain_password: str) -> Optional[User]:
        """
        Authenticates credentials against stored password hashes.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warn("Authentication failed. User not found.", email=email)
            return None

        if not verify_password(plain_password, user.password_hash):
            logger.warn("Authentication failed. Password mismatch.", email=email)
            return None

        if not user.is_active:
            logger.warn("Authentication failed. Account inactive.", email=email)
            return None

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
    async def rotate_session_token(db: AsyncSession, old_token: str) -> Tuple[str, str]:
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

        # Generate new session
        return await AuthService.create_user_session(db, user)

    @staticmethod
    async def revoke_user_session(db: AsyncSession, token: str) -> None:
        """
        Revokes a refresh token, signing the user out.
        """
        query = select(RefreshToken).where(RefreshToken.token == token)
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True
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
    async def verify_email_token(db: AsyncSession, token: str) -> bool:
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
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
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
        await db.commit()
        logger.info("Password reset successfully", user_id=str(user.id))
        return True

    @staticmethod
    async def authenticate_google_user(db: AsyncSession, email: str, first_name: str, last_name: str) -> User:
        """
        OAuth linking flow. Logs in existing users by matching email, or creates a new user on first login.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            # Explicitly mark user active & verified on Google login match
            user.is_verified = True
            await db.commit()
            logger.info("Google OAuth login match success", user_id=str(user.id), email=email)
            return user
            
        # First login case: Create user profile with empty password context
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
        await db.commit()
        await db.refresh(user)
        logger.info("First login google OAuth account created", user_id=str(user.id), email=email)
        return user
