import pytest
import io
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.auth.models import User, Role, Permission, AuditLog
from src.modules.auth.services import AuthService, RBACService


@pytest.mark.asyncio
async def test_default_roles_seeded(db_session: AsyncSession):
    """
    Verify that migration execution successfully seeded default roles and permissions.
    """
    query = select(Role).where(Role.name == "ORG_OWNER")
    result = await db_session.execute(query)
    role = result.scalar_one_or_none()
    assert role is not None
    assert role.role_type == "ORGANIZATION"


@pytest.mark.asyncio
async def test_profile_retrieval_and_update(client: TestClient, db_session: AsyncSession):
    """
    Test profile query details and updates, asserting audit logs trigger.
    """
    # 1. Sign up user
    client.post("/api/v1/auth/signup", json={
        "email": "profile@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Profile",
        "last_name": "Tester"
    })
    
    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "profile@datasense.ai",
        "password": "SecurePassword123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get profile
    get_resp = client.get("/api/v1/auth/profile", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "profile@datasense.ai"

    # 4. Update profile fields
    update_data = {
        "username": "profile_tester",
        "phone": "+1234567890",
        "bio": "Senior Analyst",
        "timezone": "EST"
    }
    put_resp = client.put("/api/v1/auth/profile", json=update_data, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["username"] == "profile_tester"
    assert put_resp.json()["timezone"] == "EST"

    # 5. Verify security audit log recorded
    query = select(User).where(User.email == "profile@datasense.ai")
    res = await db_session.execute(query)
    user = res.scalar_one()
    
    audit_query = select(AuditLog).where(AuditLog.user_id == user.id, AuditLog.action == "PROFILE_UPDATE")
    audit_res = await db_session.execute(audit_query)
    assert audit_res.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_avatar_upload_restrictions(client: TestClient, db_session: AsyncSession):
    """
    Test avatar upload validations (unsupported files blocking).
    """
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "profile@datasense.ai",
        "password": "SecurePassword123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload unsupported file (e.g. text file instead of image)
    file_payload = {"file": ("test.txt", io.BytesIO(b"dummy text content"), "text/plain")}
    response = client.post("/api/v1/auth/profile/avatar", files=file_payload, headers=headers)
    assert response.status_code == 400
    assert "Unsupported format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rbac_permission_enforcement(client: TestClient, db_session: AsyncSession):
    """
    Asserts that listing roles requires 'roles:read' permission (rejections check).
    """
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "profile@datasense.ai",
        "password": "SecurePassword123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Default users do not have 'roles:read' assigned
    response = client.get("/api/v1/auth/roles", headers=headers)
    assert response.status_code == 403
    assert "Missing required permission" in response.json()["detail"]
