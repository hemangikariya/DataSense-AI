from typing import Dict, Any, List
import uuid
from fastapi import Depends, Header, HTTPException, status, Request
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


async def verify_organization_access(
    org_id: uuid.UUID = Header(..., alias="X-Organization-ID"),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
) -> uuid.UUID:
    """
    Enforces user is authenticated and belongs to the specified organization.
    """
    user_org_id = user_context.get("org_id")
    if not user_org_id or user_org_id != str(org_id):
        logger.error("Tenant boundary validation failed: organization mismatch", user_org_id=user_org_id, target_org_id=str(org_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Access to this organization is denied."
        )
    return org_id


async def verify_workspace_access(
    workspace_id: uuid.UUID = Header(..., alias="X-Workspace-ID"),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
) -> uuid.UUID:
    """
    Enforces user is authenticated and has access membership in the target workspace.
    """
    # 1. Enforce parent organization validation first
    user_org_id = user_context.get("org_id")
    user_id = user_context.get("sub")
    user_role = user_context.get("org_role")
    
    # 2. Query workspace parent organization mapping
    from src.modules.organizations.models import Workspace, WorkspaceMember
    from sqlalchemy import select
    
    ws_query = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_query)
    workspace = ws_result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
        
    if str(workspace.organization_id) != user_org_id:
        logger.error("Tenant boundary validation: Cross-tenant workspace query rejected.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden. Cross-tenant query.")

    # 3. Check membership if user is not ORG_OWNER / ORG_ADMIN
    if user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        mem_query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == uuid.UUID(user_id)
        )
        mem_result = await db.execute(mem_query)
        if not mem_result.scalar_one_or_none():
            logger.error("Tenant boundary validation: member access denied to workspace", user_id=user_id, workspace_id=str(workspace_id))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden. Not a workspace member.")

    return workspace_id


class PermissionRequired:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        request: Request,
        user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
        db: AsyncSession = Depends(get_db)
    ) -> bool:
        """
        Validates request permissions matching Org and Workspace roles lists.
        """
        user_id = uuid.UUID(user_context.get("sub"))
        org_role = user_context.get("org_role")
        
        # 1. Super Admin override
        if org_role == "SUPER_ADMIN":
            return True
            
        # 2. Extract active Workspace role context
        workspace_id_str = request.headers.get("X-Workspace-ID")
        workspace_role = None
        if workspace_id_str:
            try:
                ws_id = uuid.UUID(workspace_id_str)
                from src.modules.organizations.models import WorkspaceMember
                from sqlalchemy import select
                member_query = select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == ws_id,
                    WorkspaceMember.user_id == user_id
                )
                member_result = await db.execute(member_query)
                member = member_result.scalar_one_or_none()
                if member:
                    workspace_role = member.workspace_role
            except Exception:
                pass

        # 3. Accumulate active roles
        roles_to_check = []
        if org_role:
            roles_to_check.append(org_role)
        if workspace_role:
            roles_to_check.append(workspace_role)

        # 4. Check loaded role permissions mappings
        from src.modules.auth.models import Role
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(Role).where(Role.name.in_(roles_to_check)).options(selectinload(Role.permissions))
        result = await db.execute(query)
        roles = result.scalars().all()
        
        for r in roles:
            for p in r.permissions:
                if p.name == self.required_permission:
                    return True

        logger.error(
            "Access denied: permission check failed",
            user_id=str(user_id),
            permission=self.required_permission,
            active_roles=roles_to_check
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden. Missing required permission: {self.required_permission}"
        )
