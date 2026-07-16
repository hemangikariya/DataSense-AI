import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, pattern="^[a-z0-9-]+$")
    settings: Optional[Dict[str, Any]] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    settings: Dict[str, Any]

    class Config:
        from_attributes = True


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, pattern="^[a-z0-9-]+$")
    settings: Optional[Dict[str, Any]] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    settings: Dict[str, Any]

    class Config:
        from_attributes = True


class MemberInviteRequest(BaseModel):
    email: EmailStr
    role: str = Field("WS_VIEWER", pattern="^(WS_ADMIN|WS_ANALYST|WS_VIEWER)$")


class MemberInviteResponse(BaseModel):
    message: str
    membership_id: uuid.UUID


class WorkspaceMemberResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    workspace_role: str

    class Config:
        from_attributes = True
