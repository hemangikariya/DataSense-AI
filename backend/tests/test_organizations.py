import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.auth.models import User
from src.modules.organizations.models import Organization, Workspace, WorkspaceMember


@pytest.mark.asyncio
async def test_organization_and_workspace_lifecycle(client: TestClient, db_session: AsyncSession):
    """
    Test complete lifecycle of organization creation, workspace provisioning and workspace memberships.
    """
    # 1. Sign up owner user
    signup_data = {
        "email": "org_owner@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Org",
        "last_name": "Owner"
    }
    client.post("/api/v1/auth/signup", json=signup_data)
    
    # 2. Login to get authenticated context token
    login_response = client.post("/api/v1/auth/login", json={
        "email": "org_owner@datasense.ai",
        "password": "SecurePassword123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Organization
    org_data = {
        "name": "Beta Corporation",
        "slug": "beta-corp",
        "settings": {"tier": "enterprise"}
    }
    org_response = client.post("/api/v1/auth/signup", json={
        "email": "org_owner_new@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Owner",
        "last_name": "New"
    })
    
    login_new = client.post("/api/v1/auth/login", json={
        "email": "org_owner_new@datasense.ai",
        "password": "SecurePassword123"
    })
    new_token = login_new.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}
    
    create_org_response = client.post("/api/v1/organizations", json=org_data, headers=new_headers)
    assert create_org_response.status_code == 201
    org_id = create_org_response.json()["id"]

    # 4. Create Workspace inside organization
    ws_data = {
        "name": "Finance Analytics",
        "slug": "finance-analytics",
        "settings": {"retention_days": 30}
    }
    # Pass org context headers
    new_headers["X-Organization-ID"] = org_id
    
    create_ws_response = client.post("/api/v1/workspaces", json=ws_data, headers=new_headers)
    assert create_ws_response.status_code == 201
    ws_id = create_ws_response.json()["id"]

    # 5. Verify Workspace exists in Database
    query = select(Workspace).where(Workspace.id == uuid.UUID(ws_id))
    result = await db_session.execute(query)
    workspace = result.scalar_one_or_none()
    assert workspace is not None
    assert workspace.name == "Finance Analytics"


@pytest.mark.asyncio
async def test_tenant_boundary_isolation(client: TestClient, db_session: AsyncSession):
    """
    Enforces that User A from Tenant A cannot access User B's Workspace from Tenant B (403 Forbidden check).
    """
    # 1. Create Tenant A owner user
    client.post("/api/v1/auth/signup", json={
        "email": "tenant_a@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Tenant",
        "last_name": "A"
    })
    login_a = client.post("/api/v1/auth/login", json={
        "email": "tenant_a@datasense.ai",
        "password": "SecurePassword123"
    })
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    create_org_a = client.post("/api/v1/organizations", json={"name": "Org A", "slug": "org-a"}, headers=headers_a)
    org_a_id = create_org_a.json()["id"]
    headers_a["X-Organization-ID"] = org_a_id

    # Create Workspace A
    create_ws_a = client.post("/api/v1/workspaces", json={"name": "WS A", "slug": "ws-a"}, headers=headers_a)
    ws_a_id = create_ws_a.json()["id"]

    # 2. Create Tenant B owner user
    client.post("/api/v1/auth/signup", json={
        "email": "tenant_b@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Tenant",
        "last_name": "B"
    })
    login_b = client.post("/api/v1/auth/login", json={
        "email": "tenant_b@datasense.ai",
        "password": "SecurePassword123"
    })
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    create_org_b = client.post("/api/v1/organizations", json={"name": "Org B", "slug": "org-b"}, headers=headers_b)
    org_b_id = create_org_b.json()["id"]
    headers_b["X-Organization-ID"] = org_b_id

    # Create Workspace B
    create_ws_b = client.post("/api/v1/workspaces", json={"name": "WS B", "slug": "ws-b"}, headers=headers_b)
    ws_b_id = create_ws_b.json()["id"]

    # 3. Cross Tenant Intrusion Check: Tenant A tries to access Workspace B
    headers_a["X-Workspace-ID"] = ws_b_id
    response = client.get(f"/api/v1/workspaces/{ws_b_id}", headers=headers_a)
    
    # Assert query is rejected with 403 Forbidden boundary check
    assert response.status_code == 403
