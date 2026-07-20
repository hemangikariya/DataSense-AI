import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import (
    get_db,
    verify_workspace_access,
    PermissionRequired
)
from src.modules.profiling.schemas import (
    DatasetProfileResponse,
    ColumnProfileResponse,
    QualityReportResponse,
    RecommendationResponse,
    OutlierSummaryResponse,
    CorrelationResponse
)
from src.modules.profiling.services import ProfilingService

router = APIRouter(prefix="/datasets", tags=["Data Profiling & Quality Engine"])


@router.get("/{id}/profile", response_model=DatasetProfileResponse, dependencies=[Depends(PermissionRequired("profile:read"))])
async def get_dataset_profile(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the complete profile data of the latest dataset version (cached in Redis).
    """
    profile = await ProfilingService.get_profile(db, id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset profile not found.")
    return profile


@router.get("/{id}/quality", response_model=QualityReportResponse, dependencies=[Depends(PermissionRequired("quality:read"))])
async def get_dataset_quality(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves completeness, uniqueness, validity, accuracy, and consistency scores.
    """
    report = await ProfilingService.get_quality_report(db, id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data quality report not found.")
    return report


@router.get("/{id}/statistics", dependencies=[Depends(PermissionRequired("profile:read"))])
async def get_dataset_statistics(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves basic statistics (row count, column count, memory, file size).
    """
    stats = await ProfilingService.get_statistics(db, id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset statistics not found.")
    return stats


@router.get("/{id}/columns", response_model=List[ColumnProfileResponse], dependencies=[Depends(PermissionRequired("profile:read"))])
async def get_dataset_columns(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists detailed profiles of columns (null percentages, unique counts, sample lists).
    """
    return await ProfilingService.list_column_profiles(db, id)


@router.get("/{id}/correlation", dependencies=[Depends(PermissionRequired("profile:read"))])
async def get_dataset_correlation(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves computed Pearson and Spearman correlation matrices.
    """
    matrix = await ProfilingService.get_correlation(db, id)
    if matrix is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Correlation matrix unavailable.")
    return {
        "dataset_id": id,
        "version_number": await ProfilingService.get_latest_dataset_version(db, id),
        "correlation_matrix": matrix
    }


@router.get("/{id}/recommendations", response_model=List[RecommendationResponse], dependencies=[Depends(PermissionRequired("quality:read"))])
async def get_dataset_recommendations(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves data remediation recommendations (Low/Medium/High/Critical severity suggestions).
    """
    return await ProfilingService.list_recommendations(db, id)


@router.get("/{id}/quality/history", response_model=List[QualityReportResponse], dependencies=[Depends(PermissionRequired("quality:read"))])
async def get_dataset_quality_history(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves historical quality scores for every uploaded version to map data quality trends.
    """
    return await ProfilingService.get_quality_history(db, id)


@router.get("/{id}/outliers", response_model=List[OutlierSummaryResponse], dependencies=[Depends(PermissionRequired("profile:read"))])
async def get_dataset_outliers(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists numerical columns containing outliers based on IQR bounds check.
    """
    return await ProfilingService.get_outliers(db, id)


@router.get("/{id}/distribution", dependencies=[Depends(PermissionRequired("profile:read"))])
async def get_dataset_column_distribution(
    id: uuid.UUID,
    column_name: str = Query(..., description="Target numeric/string column name"),
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves min/max/mean, standard deviations, skewness, kurtosis, percentiles, and sample arrays for a column.
    """
    dist = await ProfilingService.get_distribution(db, id, column_name)
    if not dist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column distribution statistics not found.")
    return dist
