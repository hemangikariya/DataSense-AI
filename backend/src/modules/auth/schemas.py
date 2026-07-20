import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters password")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    workspace_id: Optional[uuid.UUID] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    org_role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class OrganizationInfo(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class SignupResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# --- Phase 2C Schemas ---

class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    username: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    timezone: str
    language: str
    theme_preference: str
    org_role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1)
    last_name: Optional[str] = Field(None, min_length=1)
    username: Optional[str] = Field(None, min_length=3, pattern="^[a-zA-Z0-9_-]+$")
    phone: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme_preference: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr


class PermissionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    role_type: str
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    role_type: str = Field("WORKSPACE", pattern="^(ORGANIZATION|WORKSPACE|SYSTEM)$")
    permissions: List[str] = []  # List of permission names to assign


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: List[str] = []
