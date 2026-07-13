from typing import Dict, Any
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db_session
from src.core.cache import redis_manager
from src.core.storage import storage_manager
from src.core.security import decode_jwt_token
from src.core.logging import logger

async def get_db() -> AsyncSession:
    """
    Dependency injection route resource for database async transactions.
    """
    async for session in get_db_session():
        yield session


def get_redis_client():
    """
    Injectable cache client reference.
    """
    return redis_manager.client


def get_minio_client():
    """
    Injectable object storage client reference.
    """
    return storage_manager.client


async def get_authenticated_user_context(
    authorization: str = Header(..., description="OAuth2 Bearer access token")
) -> Dict[str, Any]:
    """
    Dependency injection validating active user JWT contexts.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token headers required."
        )
    
    token = authorization.split(" ")[1]
    claims = decode_jwt_token(token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or expired session token."
        )
    
    # Context bindings
    logger.bind(
        user_id=claims.get("sub"),
        org_id=claims.get("org_id"),
        workspace_id=claims.get("workspace_id")
    )
    return claims
