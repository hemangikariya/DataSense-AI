import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReportSectionCreate(BaseModel):
    section_type: str = Field(..., pattern="^(TEXT|CHART|TABLE|KPI)$")
    title: str = Field(..., min_length=1)
    content_text: Optional[str] = None
    source_widget_id: Optional[uuid.UUID] = None
    source_dataset_id: Optional[uuid.UUID] = None
    sort_order: int = 0


class ReportSectionResponse(BaseModel):
    id: uuid.UUID
    section_type: str
    title: str
    content_text: Optional[str] = None
    source_widget_id: Optional[uuid.UUID] = None
    source_dataset_id: Optional[uuid.UUID] = None
    sort_order: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    sections: List[ReportSectionCreate] = []


class ReportResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    creator_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_template: bool
    template_name: Optional[str] = None
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    sections: List[ReportSectionResponse] = []

    class Config:
        from_attributes = True


class ScheduledReportCreate(BaseModel):
    schedule_type: str = Field(..., pattern="^(Daily|Weekly|Monthly|Cron)$")
    cron_expression: str = Field(..., min_length=5)
    timezone: str = "UTC"
    is_enabled: bool = True
    recipients_emails_json: Optional[List[str]] = None


class ScheduledReportResponse(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    workspace_id: uuid.UUID
    schedule_type: str
    cron_expression: str
    timezone: str
    is_enabled: bool
    recipients_emails_json: Optional[List[str]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ReportHistoryResponse(BaseModel):
    id: uuid.UUID
    report_id: Optional[uuid.UUID] = None
    workspace_id: uuid.UUID
    export_format: str
    status: str
    storage_path: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PredictionJobCreate(BaseModel):
    dataset_id: uuid.UUID
    algorithm: str = Field(..., pattern="^(Linear Regression|Polynomial Regression|Moving Average Forecast|Exponential Smoothing|Basic Classification|K-Means Clustering)$")
    target_column: str = Field(..., min_length=1)
    parameters_json: Optional[Dict[str, Any]] = None


class PredictionResultResponse(BaseModel):
    id: uuid.UUID
    predictions_json: Dict[str, Any]
    confidence_score: float
    metrics_json: Optional[Dict[str, Any]] = None
    feature_importance_json: Optional[Dict[str, Any]] = None
    plain_explanation: str
    limitations: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PredictionJobResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    dataset_id: uuid.UUID
    creator_id: Optional[uuid.UUID] = None
    algorithm: str
    target_column: str
    parameters_json: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime.datetime
    results: List[PredictionResultResponse] = []

    class Config:
        from_attributes = True
