from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
import bcrypt
from src.config import settings
from src.core.logging import logger

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check plain password against stored bcrypt hash context.
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error("Bcrypt password verification check failed", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """
    Generate bcrypt hash from plain passwords.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """
    Assembles signed JWT tokens with claims payload mapping.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        logger.error("JWT encryption token generation failed", error=str(e))
        raise


def create_access_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates JWT claims signatures.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warn("JWT decryption token signature check failed", error=str(e))
        return None
