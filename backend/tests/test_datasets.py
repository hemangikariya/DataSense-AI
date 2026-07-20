import pytest
import io
import json
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.datasets.models import Dataset, DatasetMetadata, DatasetVersion
from src.modules.datasets.services import DatasetService
from src.modules.datasets.tasks import async_process_dataset


@pytest.fixture
def mock_celery_delay():
    with patch("src.modules.datasets.tasks.process_dataset_upload_task.delay") as mock:
        yield mock


@pytest.fixture
def mock_storage_put():
    with patch("src.core.storage.storage_manager.client.put_object") as mock:
        yield mock


@pytest.fixture
def mock_storage_get():
    with patch("src.core.storage.storage_manager.client.get_object") as mock:
        # Mock returns simple CSV payload
        mock_response = MagicMock()
        mock_response.read.return_value = b"col1,col2\n1,foo\n2,bar\n"
        mock.return_value = mock_response
        yield mock


@pytest.mark.asyncio
async def test_dataset_upload_flow(
    client: TestClient,
    db_session: AsyncSession,
    mock_celery_delay,
    mock_storage_put
):
    """
    Test dataset uploading initiation route, verifying form parsing and S3 upload triggers.
    """
    # 1. Sign up and Login
    client.post("/api/v1/auth/signup", json={
        "email": "dataset@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Data",
        "last_name": "Tester"
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "dataset@datasense.ai",
        "password": "SecurePassword123"
    })
    token = login_resp.json()["access_token"]
    user_id = login_resp.json()["user"]["id"]

    # Assign organization context manually
    from src.modules.auth.models import User
    user_query = select(User).where(User.id == uuid.UUID(user_id))
    user_res = await db_session.execute(user_query)
    user = user_res.scalar_one()
    org_id = uuid.uuid4()
    user.organization_id = org_id
    await db_session.commit()

    # 2. Create organization workspace context
    from src.modules.organizations.models import Workspace
    workspace = Workspace(
        organization_id=org_id,
        name="Data Sandbox",
        slug="data-sandbox"
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)

    # Make the user ORG_OWNER to bypass RBAC on tests
    user.org_role = "ORG_OWNER"
    await db_session.commit()

    # 3. Request upload
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Workspace-ID": str(workspace.id),
        "X-Organization-ID": str(org_id)
    }
    
    file_payload = {
        "file": ("sample.csv", io.BytesIO(b"col1,col2\n1,foo\n2,bar\n"), "text/csv")
    }
    form_data = {
        "name": "Metrics Dataset",
        "description": "Sandbox ingestion source",
        "tags_json": '["finance", "monthly"]'
    }

    response = client.post(
        "/api/v1/datasets",
        files=file_payload,
        data=form_data,
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Metrics Dataset"
    assert response.json()["status"] == "Processing"

    # Verify background Celery task scheduled
    mock_celery_delay.assert_called_once()
    # Verify S3 upload triggered
    mock_storage_put.assert_called()


@pytest.mark.asyncio
async def test_dataset_celery_processing(
    db_session: AsyncSession,
    mock_storage_get,
    mock_storage_put
):
    """
    Simulates background Celery worker processing of raw file bytes.
    """
    # Create dataset record in db
    org_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    dataset = Dataset(
        organization_id=org_id,
        workspace_id=workspace_id,
        name="Async Ingestion Test",
        format="CSV",
        storage_path="datasets/dummy.csv"
    )
    db_session.add(dataset)
    await db_session.commit()
    await db_session.refresh(dataset)

    # Execute async parsing function directly
    await async_process_dataset(
        dataset_id=dataset.id,
        storage_path="datasets/dummy.csv",
        original_filename="dummy.csv",
        file_size=20,
        content_type="text/csv",
        user_id=None
    )

    # Refresh dataset state from DB
    query = select(Dataset).where(Dataset.id == dataset.id).options(selectinload(Dataset.tags))
    result = await db_session.execute(query)
    updated_dataset = result.scalar_one()

    # Assert success states
    assert updated_dataset.status == "Ready"
    assert updated_dataset.hash is not None

    # Verify metadata created
    meta_query = select(DatasetMetadata).where(DatasetMetadata.dataset_id == dataset.id)
    meta_res = await db_session.execute(meta_query)
    metadata = meta_res.scalar_one()
    assert metadata.rows_count == 2
    assert metadata.columns_count == 2


@pytest.mark.asyncio
async def test_soft_delete_and_restore(client: TestClient, db_session: AsyncSession):
    """
    Verify soft delete changes flag state and restoration returns it to active.
    """
    # Query an existing dataset
    query = select(Dataset)
    result = await db_session.execute(query)
    dataset = result.scalars().first()
    if not dataset:
        return  # Skip if no dataset populated from earlier tests

    # Sign in and grab workspace headers from test contexts
    # (Using service layer directly to bypass client header configurations is fast and robust)
    success = await DatasetService.delete_dataset(db_session, dataset.id, uuid.uuid4())
    assert success is True

    # Assert soft deleted flag updated
    db_session.expire_all()
    q = select(Dataset).where(Dataset.id == dataset.id)
    res = await db_session.execute(q)
    d = res.scalar_one()
    assert d.is_deleted is True
    assert d.deleted_at is not None

    # Restore dataset
    restore_success = await DatasetService.restore_dataset(db_session, dataset.id, uuid.uuid4())
    assert restore_success is True
    assert d.is_deleted is False
