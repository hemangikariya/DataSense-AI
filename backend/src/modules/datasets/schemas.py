import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    tags: List[str] = []


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DatasetVersionResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    storage_path: str
    hash: str
    change_log: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DatasetMetadataResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    original_filename: str
    file_size: int
    file_type: str
    rows_count: Optional[int] = None
    columns_count: Optional[int] = None
    schema_json: Optional[Dict[str, str]] = None
    summary_stats_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DatasetResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    creator_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    status: str
    format: str
    storage_path: str
    hash: Optional[str] = None
    version: int
    parent_dataset_id: Optional[uuid.UUID] = None
    source: str
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tags: List[str] = []

    class Config:
        from_attributes = True


class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    datatypes: Dict[str, str]
    missing_values: Dict[str, int]
    duplicate_rows: int
    row_count: int
    preview_data: List[Dict[str, Any]]
