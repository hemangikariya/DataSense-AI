import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import (
    get_db,
    get_authenticated_user_context,
    verify_organization_access,
    verify_workspace_access
)
from src.core.logging import logger
from src.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    MemberInviteRequest,
    MemberInviteResponse,
    WorkspaceMemberResponse
)
from src.modules.organizations.services import (
    OrganizationService,
    WorkspaceService,
    MembershipService
)

router = APIRouter(prefix="", tags=["Organizations & Workspaces"])


# --- Organizations ---

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    schema: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    owner_id = uuid.UUID(user_context.get("sub"))
    try:
        org = await OrganizationService.create_organization(db, schema, owner_id)
        return org
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{id}", response_model=OrganizationResponse, status_code=status.HTTP_200_OK)
async def get_organization_details(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    # Enforce tenant isolation check
    user_org_id = user_context.get("org_id")
    if not user_org_id or user_org_id != str(id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this organization.")

    org = await OrganizationService.get_organization(db, id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


@router.put("/organizations/{id}", response_model=OrganizationResponse, status_code=status.HTTP_200_OK)
async def update_organization(
    id: uuid.UUID,
    schema: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    user_org_id = user_context.get("org_id")
    user_role = user_context.get("org_role")
    
    if not user_org_id or user_org_id != str(id) or user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Admin role required.")

    org = await OrganizationService.update_organization(db, id, schema)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


@router.delete("/organizations/{id}", status_code=status.HTTP_200_OK)
async def delete_organization(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    user_org_id = user_context.get("org_id")
    user_role = user_context.get("org_role")
    
    if not user_org_id or user_org_id != str(id) or user_role != "ORG_OWNER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Owner role required.")

    success = await OrganizationService.delete_organization(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return {"message": "Organization deleted successfully."}


@router.post("/organizations/switch", status_code=status.HTTP_200_OK)
async def switch_active_organization(
    target_org_id: uuid.UUID = Header(..., alias="X-Organization-ID"),
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    # Switches organization context session
    user_id = uuid.UUID(user_context.get("sub"))
    success = await OrganizationService.switch_active_organization(db, user_id, target_org_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to switch organization. Invalid target ID.")
    return {"message": "Organization context switched successfully."}


# --- Workspaces ---

@router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    schema: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    org_id = uuid.UUID(user_context.get("org_id"))
    user_role = user_context.get("org_role")
    
    if user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only organization admins can create workspaces.")

    try:
        ws = await WorkspaceService.create_workspace(db, org_id, schema)
        return ws
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/workspaces/{id}", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK)
async def get_workspace_details(
    id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    ws = await WorkspaceService.get_workspace(db, id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return ws


@router.put("/workspaces/{id}", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK)
async def update_workspace(
    schema: WorkspaceUpdate,
    id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    user_role = user_context.get("org_role")
    if user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace settings updates require admin role.")

    ws = await WorkspaceService.update_workspace(db, id, schema)
    return ws


@router.delete("/workspaces/{id}", status_code=status.HTTP_200_OK)
async def delete_workspace(
    id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    user_role = user_context.get("org_role")
    if user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace deletion requires admin role.")

    success = await WorkspaceService.delete_workspace(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return {"message": "Workspace deleted successfully."}


@router.get("/workspaces", response_model=List[WorkspaceResponse], status_code=status.HTTP_200_OK)
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    org_id = uuid.UUID(user_context.get("org_id"))
    user_id = uuid.UUID(user_context.get("sub"))
    user_role = user_context.get("org_role")
    
    is_admin = user_role in ["ORG_OWNER", "ORG_ADMIN"]
    workspaces = await WorkspaceService.list_workspaces(db, org_id, user_id, is_admin)
    return workspaces


# --- Memberships ---

@router.post("/workspaces/{id}/members", response_model=MemberInviteResponse, status_code=status.HTTP_200_OK)
async def invite_member_to_workspace(
    schema: MemberInviteRequest,
    id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    user_role = user_context.get("org_role")
    if user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can invite members.")

    try:
        member = await MembershipService.invite_member(db, id, schema.email, schema.role)
        if not member:
            raise HTTPException(status_code=400, detail="Invited email user not found in systems.")
        return {"message": "User invited to workspace successfully.", "membership_id": member.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/workspaces/{id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_member_from_workspace(
    user_id: uuid.UUID,
    id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    user_role = user_context.get("org_role")
    if user_role not in ["ORG_OWNER", "ORG_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can remove members.")

    success = await MembershipService.remove_member(db, id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace member record not found.")
    return {"message": "Member removed from workspace successfully."}


@router.get("/workspaces/{id}/members", response_model=List[WorkspaceMemberResponse], status_code=status.HTTP_200_OK)
async def list_workspace_members(
    id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    members = await MembershipService.list_members(db, id)
    return members
