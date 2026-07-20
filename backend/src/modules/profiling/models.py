import datetime
import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UUID, Integer, BigInteger, Float, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    rows_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    columns_count: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    memory_usage: Mapped[int] = mapped_column(BigInteger, nullable=False)
    missing_values: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(BigInteger, nullable=False)
    correlation_matrix_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    column_profiles: Mapped[List["ColumnProfile"]] = relationship(
        "ColumnProfile", back_populates="dataset_profile", cascade="all, delete-orphan"
    )


class ColumnProfile(Base):
    __tablename__ = "column_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unique_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    missing_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    null_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    cardinality: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Numeric stats
    min_val: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_val: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mean_val: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    median_val: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mode_val: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    std_dev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    variance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    skewness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    kurtosis: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percentiles_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 25, 50, 75, 95, 99
    
    # Text stats
    avg_length: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    empty_strings_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Date stats
    earliest_date: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latest_date: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invalid_date_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    date_range: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Outliers
    sample_values_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outliers_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    outliers_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    dataset_profile: Mapped[DatasetProfile] = relationship(back_populates="column_profiles")


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, nullable=False)
    validity_score: Mapped[float] = mapped_column(Float, nullable=False)
    uniqueness_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Drift Columns
    previous_version_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_difference: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    schema_changes_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # Low, Medium, High, Critical
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # Duplicates, Nulls, Text, Dates, Outliers
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
