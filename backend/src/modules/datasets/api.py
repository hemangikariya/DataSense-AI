import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import (
    get_db,
    get_authenticated_user_context,
    verify_workspace_access,
    PermissionRequired
)
from src.modules.datasets.schemas import (
    DatasetResponse,
    DatasetCreate,
    DatasetUpdate,
    DatasetVersionResponse,
    DatasetMetadataResponse,
    DatasetPreviewResponse
)
from src.modules.datasets.services import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets Management"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("dataset:create"))])
async def upload_dataset(
    request: Request,
    file: UploadFile = File(..., description="Dataset CSV/XLSX/JSON/Parquet payload"),
    name: str = Form(..., description="Dataset name"),
    description: Optional[str] = Form(None, description="Dataset description"),
    tags_json: Optional[str] = Form(None, description="JSON string list of tags"),
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests and processes a dataset file under the active workspace, starting background ingestion.
    """
    creator_id = uuid.UUID(user_context.get("sub"))
    org_id = uuid.UUID(user_context.get("org_id"))
    ip_addr = request.client.host if request.client else None

    # Parse tags JSON list safely
    tags = []
    if tags_json:
        try:
            tags = json.loads(tags_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON array format in tags_json Form field.")

    schema = DatasetCreate(name=name, description=description, tags=tags)
    file_content = await file.read()

    try:
        dataset = await DatasetService.create_dataset(
            db=db,
            org_id=org_id,
            workspace_id=workspace_id,
            creator_id=creator_id,
            schema=schema,
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type,
            file_size=len(file_content),
            request_ip=ip_addr
        )
        return dataset
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DatasetResponse], dependencies=[Depends(PermissionRequired("dataset:read"))])
async def list_datasets(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    search: Optional[str] = Query(None, description="Search query filter"),
    tag: Optional[str] = Query(None, description="Tag lookup filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists active datasets in the workspace context.
    """
    datasets, _ = await DatasetService.list_datasets(db, workspace_id, search, tag, page, page_size)
    return datasets


@router.get("/{id}", response_model=DatasetResponse, dependencies=[Depends(PermissionRequired("dataset:read"))])
async def get_dataset_details(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves details of the target dataset.
    """
    dataset = await DatasetService.get_dataset(db, id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return dataset


@router.put("/{id}", response_model=DatasetResponse, dependencies=[Depends(PermissionRequired("dataset:update"))])
async def update_dataset(
    id: uuid.UUID,
    schema: DatasetUpdate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates dataset descriptor metadata or tag items.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    dataset = await DatasetService.update_dataset(db, id, schema, user_id, ip_addr)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return dataset


@router.delete("/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dataset:delete"))])
async def delete_dataset(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs soft delete of dataset files.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    success = await DatasetService.delete_dataset(db, id, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return {"message": "Dataset soft deleted successfully."}


@router.post("/{id}/restore", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dataset:update"))])
async def restore_dataset(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Restores a soft-deleted dataset back to active.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    success = await DatasetService.restore_dataset(db, id, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found or not deleted.")
    return {"message": "Dataset restored successfully."}


@router.get("/{id}/preview", response_model=DatasetPreviewResponse, dependencies=[Depends(PermissionRequired("dataset:read"))])
async def get_dataset_preview(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the pre-calculated preview profile for the dataset (first 100 rows).
    """
    preview = await DatasetService.get_preview(db, id)
    if not preview:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Preview unavailable or dataset processing not completed.")
    return preview


@router.get("/{id}/metadata", response_model=DatasetMetadataResponse, dependencies=[Depends(PermissionRequired("dataset:read"))])
async def get_dataset_metadata(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the column data types schema and profile summary stats.
    """
    metadata = await DatasetService.get_metadata(db, id)
    if not metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metadata profile not found.")
    return metadata


@router.get("/{id}/versions", response_model=List[DatasetVersionResponse], dependencies=[Depends(PermissionRequired("dataset:read"))])
async def get_dataset_versions(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves complete version history records.
    """
    return await DatasetService.list_versions(db, id)


@router.post("/{id}/restore-version", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dataset:update"))])
async def restore_dataset_version(
    id: uuid.UUID,
    version_number: int = Query(..., ge=1, description="Target version index key"),
    request: Request = None,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Restores the dataset file pointers to a previous historical version.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    success = await DatasetService.restore_version(db, id, version_number, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version restore failed. Invalid version identifier.")
    return {"message": f"Dataset successfully rolled back to version {version_number}."}


@router.get("/{id}/download", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dataset:read"))])
async def get_dataset_download_url(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a secure, temporary pre-signed MinIO URL to download the original dataset file.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    url = await DatasetService.get_download_url(db, id, user_id, ip_addr)
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset download pointer not found.")
    return {"download_url": url}
