import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.cache import redis_manager
from src.core.logging import logger
from src.modules.datasets.models import Dataset
from src.modules.profiling.models import DatasetProfile, ColumnProfile, QualityReport, Recommendation


class ProfilingService:
    @staticmethod
    async def get_latest_dataset_version(db: AsyncSession, dataset_id: uuid.UUID) -> int:
        query = select(Dataset.version).where(Dataset.id == dataset_id, Dataset.is_deleted == False)
        result = await db.execute(query)
        return result.scalar_one_or_none() or 1

    @staticmethod
    async def get_profile(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[DatasetProfile]:
        """
        Retrieves the profile of the latest version, utilizing Redis to cache database queries.
        """
        version = await ProfilingService.get_latest_dataset_version(db, dataset_id)
        cache_key = f"profiling:profile:{dataset_id}:{version}"
        
        # Check cache
        redis_client = redis_manager.client
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info("Serving profile data from Redis cache", dataset_id=str(dataset_id))
                data = json.loads(cached)
                # Map back to mock return or response format (handled by Pydantic directly if we parse)
                return data

        query = select(DatasetProfile).where(
            DatasetProfile.dataset_id == dataset_id,
            DatasetProfile.version_number == version
        ).options(selectinload(DatasetProfile.column_profiles))
        result = await db.execute(query)
        profile = result.scalar_one_or_none()

        if profile and redis_client:
            # Cache the serialized profile response JSON
            from src.modules.profiling.schemas import DatasetProfileResponse
            serialized = DatasetProfileResponse.model_validate(profile).model_dump_json()
            await redis_client.set(cache_key, serialized, ex=3600)  # cache for 1 hour

        return profile

    @staticmethod
    async def get_quality_report(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[QualityReport]:
        """
        Returns the quality report, utilizing Redis caching.
        """
        version = await ProfilingService.get_latest_dataset_version(db, dataset_id)
        cache_key = f"profiling:quality:{dataset_id}:{version}"
        
        redis_client = redis_manager.client
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        query = select(QualityReport).where(
            QualityReport.dataset_id == dataset_id,
            QualityReport.version_number == version
        )
        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if report and redis_client:
            from src.modules.profiling.schemas import QualityReportResponse
            serialized = QualityReportResponse.model_validate(report).model_dump_json()
            await redis_client.set(cache_key, serialized, ex=3600)

        return report

    @staticmethod
    async def get_statistics(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        profile = await ProfilingService.get_profile(db, dataset_id)
        if not profile:
            return None
            
        # If it is a dictionary (from cache), handle keys directly
        if isinstance(profile, dict):
            return {
                "rows_count": profile["rows_count"],
                "columns_count": profile["columns_count"],
                "file_size": profile["file_size"],
                "memory_usage": profile["memory_usage"]
            }
            
        return {
            "rows_count": profile.rows_count,
            "columns_count": profile.columns_count,
            "file_size": profile.file_size,
            "memory_usage": profile.memory_usage
        }

    @staticmethod
    async def list_column_profiles(db: AsyncSession, dataset_id: uuid.UUID) -> List[ColumnProfile]:
        profile = await ProfilingService.get_profile(db, dataset_id)
        if not profile:
            return []
        if isinstance(profile, dict):
            return profile.get("column_profiles", [])
        return profile.column_profiles

    @staticmethod
    async def get_correlation(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        profile = await ProfilingService.get_profile(db, dataset_id)
        if not profile:
            return None
        if isinstance(profile, dict):
            return profile.get("correlation_matrix_json", {})
        return profile.correlation_matrix_json

    @staticmethod
    async def list_recommendations(db: AsyncSession, dataset_id: uuid.UUID) -> List[Recommendation]:
        version = await ProfilingService.get_latest_dataset_version(db, dataset_id)
        query = select(Recommendation).where(
            Recommendation.dataset_id == dataset_id,
            Recommendation.version_number == version
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_quality_history(db: AsyncSession, dataset_id: uuid.UUID) -> List[QualityReport]:
        query = select(QualityReport).where(
            QualityReport.dataset_id == dataset_id
        ).order_by(QualityReport.version_number.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_outliers(db: AsyncSession, dataset_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Summarizes outliers across all profiled numeric columns.
        """
        columns = await ProfilingService.list_column_profiles(db, dataset_id)
        outliers = []
        for col in columns:
            col_name = col["column_name"] if isinstance(col, dict) else col.column_name
            cnt = col["outliers_count"] if isinstance(col, dict) else col.outliers_count
            pct = col["outliers_percentage"] if isinstance(col, dict) else col.outliers_percentage
            
            if cnt > 0:
                outliers.append({
                    "column_name": col_name,
                    "outliers_count": cnt,
                    "outliers_percentage": pct,
                    "method_used": "IQR"
                })
        return outliers

    @staticmethod
    async def get_distribution(db: AsyncSession, dataset_id: uuid.UUID, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Extracts distribution stats for a target column.
        """
        columns = await ProfilingService.list_column_profiles(db, dataset_id)
        for col in columns:
            name = col["column_name"] if isinstance(col, dict) else col.column_name
            if name == column_name:
                if isinstance(col, dict):
                    return {
                        "column_name": column_name,
                        "min": col.get("min_val"),
                        "max": col.get("max_val"),
                        "mean": col.get("mean_val"),
                        "median": col.get("median_val"),
                        "std_dev": col.get("std_dev"),
                        "skewness": col.get("skewness"),
                        "kurtosis": col.get("kurtosis"),
                        "percentiles": col.get("percentiles_json"),
                        "samples": col.get("sample_values_json", {}).get("samples", [])
                    }
                return {
                    "column_name": column_name,
                    "min": col.min_val,
                    "max": col.max_val,
                    "mean": col.mean_val,
                    "median": col.median_val,
                    "std_dev": col.std_dev,
                    "skewness": col.skewness,
                    "kurtosis": col.kurtosis,
                    "percentiles": col.percentiles_json,
                    "samples": col.sample_values_json.get("samples", []) if col.sample_values_json else []
                }
        return None
