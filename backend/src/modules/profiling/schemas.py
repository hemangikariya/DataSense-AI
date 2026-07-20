import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ColumnProfileResponse(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool
    unique_count: int
    duplicate_count: int
    missing_count: int
    null_percentage: float
    cardinality: float
    
    # Numeric
    min_val: Optional[str] = None
    max_val: Optional[str] = None
    mean_val: Optional[float] = None
    median_val: Optional[float] = None
    mode_val: Optional[str] = None
    std_dev: Optional[float] = None
    variance: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    percentiles_json: Optional[Dict[str, float]] = None
    
    # Text
    avg_length: Optional[float] = None
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    empty_strings_count: Optional[int] = None
    
    # Date
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    invalid_date_count: Optional[int] = None
    date_range: Optional[str] = None
    
    # Outliers & Samples
    sample_values_json: Optional[Dict[str, Any]] = None
    outliers_count: int
    outliers_percentage: float

    class Config:
        from_attributes = True


class DatasetProfileResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    rows_count: int
    columns_count: int
    file_size: int
    memory_usage: int
    missing_values: int
    duplicate_rows: int
    correlation_matrix_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    column_profiles: List[ColumnProfileResponse] = []

    class Config:
        from_attributes = True


class QualityReportResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    validity_score: float
    uniqueness_score: float
    overall_score: float
    
    # Drift
    previous_version_number: Optional[int] = None
    previous_quality_score: Optional[float] = None
    quality_difference: Optional[float] = None
    schema_changes_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    severity: str
    category: str
    description: str
    suggested_fix: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class OutlierSummaryResponse(BaseModel):
    column_name: str
    outliers_count: int
    outliers_percentage: float
    method_used: str

    class Config:
        from_attributes = True


class CorrelationResponse(BaseModel):
    dataset_id: uuid.UUID
    version_number: int
    correlation_matrix: Dict[str, Any]
