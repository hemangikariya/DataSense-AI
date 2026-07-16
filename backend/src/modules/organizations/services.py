import uuid
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from src.modules.organizations.models import Organization, Workspace, WorkspaceMember
from src.modules.auth.models import User
from src.modules.organizations.schemas import OrganizationCreate, OrganizationUpdate, WorkspaceCreate, WorkspaceUpdate


class OrganizationService:
    @staticmethod
    async def create_organization(db: AsyncSession, schema: OrganizationCreate, owner_id: uuid.UUID) -> Organization:
        """
        Creates a new organization, and assigns the initiating user as ORG_OWNER.
        """
        org = Organization(
            name=schema.name,
            slug=schema.slug,
            settings=schema.settings or {}
        )
        db.add(org)
        await db.flush()  # Extract ID

        # Link user to organization as owner
        query = select(User).where(User.id == owner_id)
        result = await db.execute(query)
        user = result.scalar_one()
        user.organization_id = org.id
        user.org_role = "ORG_OWNER"
        
        await db.commit()
        await db.refresh(org)
        logger.info("SaaS Org Created Audit", org_id=str(org.id), owner_id=str(owner_id))
        return org

    @staticmethod
    async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
        query = select(Organization).where(Organization.id == org_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_organization(db: AsyncSession, org_id: uuid.UUID, schema: OrganizationUpdate) -> Optional[Organization]:
        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            return None
        if schema.name is not None:
            org.name = schema.name
        if schema.settings is not None:
            # Merge settings
            org.settings = {**org.settings, **schema.settings}
        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def delete_organization(db: AsyncSession, org_id: uuid.UUID) -> bool:
        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            return False
        await db.delete(org)
        await db.commit()
        logger.info("SaaS Org Deleted Audit", org_id=str(org_id))
        return True

    @staticmethod
    async def switch_active_organization(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        # Check user exists
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            return False
            
        # Check user belongs to organization (or is switching organization context)
        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            return False
            
        user.organization_id = org_id
        await db.commit()
        logger.info("Tenant switcher audit log", user_id=str(user_id), new_org_id=str(org_id))
        return True


class WorkspaceService:
    @staticmethod
    async def create_workspace(db: AsyncSession, org_id: uuid.UUID, schema: WorkspaceCreate) -> Workspace:
        ws = Workspace(
            organization_id=org_id,
            name=schema.name,
            slug=schema.slug,
            settings=schema.settings or {}
        )
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        logger.info("Workspace Created Audit", workspace_id=str(ws.id), org_id=str(org_id))
        return ws

    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> Optional[Workspace]:
        query = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_workspace(db: AsyncSession, workspace_id: uuid.UUID, schema: WorkspaceUpdate) -> Optional[Workspace]:
        ws = await WorkspaceService.get_workspace(db, workspace_id)
        if not ws:
            return None
        if schema.name is not None:
            ws.name = schema.name
        if schema.settings is not None:
            ws.settings = {**ws.settings, **schema.settings}
        await db.commit()
        await db.refresh(ws)
        return ws

    @staticmethod
    async def delete_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> bool:
        ws = await WorkspaceService.get_workspace(db, workspace_id)
        if not ws:
            return False
        await db.delete(ws)
        await db.commit()
        logger.info("Workspace Deleted Audit", workspace_id=str(workspace_id))
        return True

    @staticmethod
    async def list_workspaces(db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, is_admin: bool) -> List[Workspace]:
        if is_admin:
            # Admins/Owners view all workspaces in their organization
            query = select(Workspace).where(Workspace.organization_id == org_id)
        else:
            # Members view only workspaces they are explicitly added to
            query = (
                select(Workspace)
                .join(WorkspaceMember)
                .where(Workspace.organization_id == org_id, WorkspaceMember.user_id == user_id)
            )
        result = await db.execute(query)
        return list(result.scalars().all())


class MembershipService:
    @staticmethod
    async def invite_member(db: AsyncSession, workspace_id: uuid.UUID, email: str, role: str) -> Optional[WorkspaceMember]:
        # Check user exists
        user_query = select(User).where(User.email == email)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            logger.warn("Member invitation failed: email user not registered", email=email)
            return None
            
        # Check if already a member
        member_query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id
        )
        member_result = await db.execute(member_query)
        if member_result.scalar_one_or_none():
            raise ValueError("User is already a member of this workspace.")

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.id,
            workspace_role=role
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        logger.info("Workspace Invite Member Audit", workspace_id=str(workspace_id), user_id=str(user.id), role=role)
        return member

    @staticmethod
    async def remove_member(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = delete(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id
        )
        result = await db.execute(stmt)
        await db.commit()
        
        success = result.rowcount > 0
        if success:
            logger.info("Workspace Remove Member Audit", workspace_id=str(workspace_id), user_id=str(user_id))
        return success

    @staticmethod
    async def list_members(db: AsyncSession, workspace_id: uuid.UUID) -> List[WorkspaceMember]:
        query = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        result = await db.execute(query)
        return list(result.scalars().all())
