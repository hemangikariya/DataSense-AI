import uuid
from typing import Optional
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
