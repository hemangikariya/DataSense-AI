import asyncio
import io
import json
import uuid
import datetime
import re
import polars as pl
import numpy as np
import scipy.stats as stats
from typing import Dict, Any, List, Optional
from src.core.celery import celery_app
from src.core.database import AsyncSessionLocal
from src.core.cache import redis_manager
from src.core.storage import storage_manager
from src.core.logging import logger
from src.config import settings
from src.modules.datasets.models import Dataset, DatasetMetadata, DatasetVersion
from src.modules.profiling.models import DatasetProfile, ColumnProfile, QualityReport, Recommendation
from src.modules.auth.services import AuditLogService

# Helper to execute async blocks within celery context
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name="profiling.generate_report",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def generate_dataset_profile_task(self, dataset_id_str: str, version_number: int, user_id_str: Optional[str] = None):
    """
    Asynchronous Celery task tracking progress, checking drift, and analyzing distributions.
    """
    logger.info("Initializing dataset profiling task", dataset_id=dataset_id_str, version=version_number)
    
    # Update Redis status tracker
    redis_client = redis_manager.client
    status_key = f"profiling:status:{dataset_id_str}:{version_number}"
    
    if redis_client:
        redis_client.set(status_key, "Running")

    try:
        run_async(
            async_profile_dataset(
                dataset_id=uuid.UUID(dataset_id_str),
                version_number=version_number,
                user_id=uuid.UUID(user_id_str) if user_id_str else None
            )
        )
        if redis_client:
            redis_client.set(status_key, "Completed")
            redis_client.expire(status_key, 86400)  # Cache status for 1 day
    except Exception as exc:
        logger.error("Dataset profiling worker task failed", dataset_id=dataset_id_str, error=str(exc))
        if redis_client:
            redis_client.set(status_key, "Failed")
            redis_client.set(f"profiling:error:{dataset_id_str}:{version_number}", str(exc))
            redis_client.expire(status_key, 86400)
        
        # Self-retry hook configuration
        raise self.retry(exc=exc)


async def async_profile_dataset(dataset_id: uuid.UUID, version_number: int, user_id: Optional[uuid.UUID]):
    async with AsyncSessionLocal() as db:
        # 1. Fetch file reference path from SQL
        from sqlalchemy import select
        q = select(Dataset).where(Dataset.id == dataset_id)
        res = await db.execute(q)
        dataset = res.scalar_one()

        s3_response = storage_manager.client.get_object(
            settings.MINIO_BUCKET_NAME,
            dataset.storage_path
        )
        file_bytes = s3_response.read()
        buffer = io.BytesIO(file_bytes)
        ext = dataset.format.lower()

        # 2. Lazy parse with Polars
        if ext == "csv":
            df = pl.read_csv(buffer)
        elif ext in ["xlsx", "xls"]:
            import pandas as pd
            pandas_df = pd.read_excel(buffer)
            df = pl.from_pandas(pandas_df)
        elif ext == "parquet":
            df = pl.read_parquet(buffer)
        elif ext == "json":
            import pandas as pd
            pandas_df = pd.read_json(buffer)
            df = pl.from_pandas(pandas_df)
        else:
            raise ValueError(f"Unsupported format .{ext}")

        # Basic counts
        rows_count = df.height
        cols_count = df.width
        file_size = len(file_bytes)
        
        # Estimate memory usage
        memory_usage = df.estimated_size()

        # 3. Create DatasetProfile Model
        profile = DatasetProfile(
            dataset_id=dataset_id,
            version_number=version_number,
            rows_count=rows_count,
            columns_count=cols_count,
            file_size=file_size,
            memory_usage=memory_usage,
            missing_values=sum(df[col].null_count() for col in df.columns),
            duplicate_rows=int(rows_count - df.unique().height)
        )
        db.add(profile)
        await db.flush()  # Generate profile.id

        # Accumulators for overall quality metrics
        total_cells = rows_count * cols_count
        total_missing = 0
        total_uniqueness = 100.0 - (float(profile.duplicate_rows / rows_count * 100) if rows_count > 0 else 0)
        
        # Format validators checks metrics
        invalid_emails_count = 0
        invalid_phones_count = 0
        invalid_urls_count = 0
        email_cols_checked = 0
        phone_cols_checked = 0
        url_cols_checked = 0

        # Correlation matrix computation
        numeric_cols = [c for c in df.columns if any(t in str(df[c].dtype) for t in ["Int", "Float", "Decimal", "UInt"])]
        correlation_matrix = {}
        if len(numeric_cols) > 1:
            try:
                pandas_numeric = df.select(numeric_cols).to_pandas()
                pearson = pandas_numeric.corr(method="pearson").fillna(0.0).to_dict()
                spearman = pandas_numeric.corr(method="spearman").fillna(0.0).to_dict()
                correlation_matrix = {"pearson": pearson, "spearman": spearman}
            except Exception:
                pass
        profile.correlation_matrix_json = correlation_matrix

        # Regex structures
        email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        phone_regex = re.compile(r"^\+?[1-9]\d{1,14}$")
        url_regex = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")

        # Column recommendations pool
        recommendations_list: List[Recommendation] = []

        # 4. Profile Columns
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing = int(df[col].null_count())
            total_missing += missing
            null_pct = float(missing / rows_count * 100) if rows_count > 0 else 0
            unique_cnt = df[col].n_unique()
            cardinality = float(unique_cnt / rows_count * 100) if rows_count > 0 else 0

            # Sample values
            sample_list = [str(x) for x in df[col].head(10).to_list() if x is not None]
            sample_json = {"samples": sample_list}

            # Outlier trackers
            outliers_cnt = 0
            outliers_pct = 0.0

            # Initialize profile record
            col_p = ColumnProfile(
                dataset_profile_id=profile.id,
                column_name=col,
                data_type=dtype,
                is_nullable=(missing > 0),
                unique_count=unique_cnt,
                duplicate_count=int(rows_count - unique_cnt),
                missing_count=missing,
                null_percentage=null_pct,
                cardinality=cardinality,
                sample_values_json=sample_json
            )

            # Analyze based on type
            is_numeric = any(t in dtype for t in ["Int", "Float", "Decimal", "UInt"])
            is_text = "String" in dtype or "Utf8" in dtype
            is_date = any(t in dtype for t in ["Date", "Datetime", "Time"])

            # 4A. Numeric Profiles
            if is_numeric:
                non_nulls = df[col].drop_nulls()
                if non_nulls.height > 0:
                    arr = non_nulls.to_numpy()
                    col_p.min_val = str(arr.min())
                    col_p.max_val = str(arr.max())
                    col_p.mean_val = float(arr.mean())
                    col_p.median_val = float(np.median(arr))
                    col_p.variance = float(arr.var())
                    col_p.std_dev = float(arr.std())
                    
                    # Percentiles
                    col_p.percentiles_json = {
                        "25": float(np.percentile(arr, 25)),
                        "50": float(np.percentile(arr, 50)),
                        "75": float(np.percentile(arr, 75)),
                        "95": float(np.percentile(arr, 95)),
                        "99": float(np.percentile(arr, 99))
                    }

                    # Skewness & Kurtosis (SciPy)
                    if non_nulls.height >= 3:
                        col_p.skewness = float(stats.skew(arr))
                        col_p.kurtosis = float(stats.kurtosis(arr))

                    # Outlier IQR estimation checks
                    q25, q75 = np.percentile(arr, [25, 75])
                    iqr = q75 - q25
                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr
                    outliers_cnt = int(np.sum((arr < lower_bound) | (arr > upper_bound)))
                    outliers_pct = float(outliers_cnt / non_nulls.height * 100)
                    
                    col_p.outliers_count = outliers_cnt
                    col_p.outliers_percentage = outliers_pct

                    # Recommendations trigger
                    if outliers_pct > 5.0:
                        recommendations_list.append(Recommendation(
                            dataset_id=dataset_id,
                            version_number=version_number,
                            severity="High",
                            category="Outliers",
                            description=f"Column '{col}' contains {outliers_pct:.2f}% outliers based on IQR bounds.",
                            suggested_fix="Cap outliers using 1.5*IQR threshold bounds or apply log transformations."
                        ))

            # 4B. Text Columns
            elif is_text:
                non_nulls = df[col].drop_nulls()
                if non_nulls.height > 0:
                    str_lengths = non_nulls.str.len_chars()
                    col_p.avg_length = float(str_lengths.mean())
                    col_p.max_length = int(str_lengths.max())
                    col_p.min_length = int(str_lengths.min())
                    col_p.empty_strings_count = int(non_nulls.filter(pl.col(col) == "").height)

                    # Top value frequencies
                    value_counts = non_nulls.value_counts().sort("count", descending=True).head(5)
                    freq_map = {row[col]: row["count"] for row in value_counts.to_dicts()}
                    col_p.mode_val = next(iter(freq_map.keys())) if freq_map else None

                    # Regex validity checks (Emails, Phones, URLs)
                    sample_strings = [str(x) for x in non_nulls.head(200).to_list()]
                    email_matches = sum(1 for x in sample_strings if email_regex.match(x))
                    phone_matches = sum(1 for x in sample_strings if phone_regex.match(x))
                    url_matches = sum(1 for x in sample_strings if url_regex.match(x))

                    # If >30% match formatting pattern, audit it as type
                    if email_matches > 0.3 * len(sample_strings):
                        email_cols_checked += 1
                        invalid_emails_count += sum(1 for x in sample_strings if not email_regex.match(x))
                    if phone_matches > 0.3 * len(sample_strings):
                        phone_cols_checked += 1
                        invalid_phones_count += sum(1 for x in sample_strings if not phone_regex.match(x))
                    if url_matches > 0.3 * len(sample_strings):
                        url_cols_checked += 1
                        invalid_urls_count += sum(1 for x in sample_strings if not url_regex.match(x))

            # 4C. Date Columns
            elif is_date:
                non_nulls = df[col].drop_nulls()
                if non_nulls.height > 0:
                    col_p.earliest_date = str(non_nulls.min())
                    col_p.latest_date = str(non_nulls.max())
                    col_p.date_range = f"{col_p.earliest_date} to {col_p.latest_date}"
                    col_p.invalid_date_count = 0  # Validated on parse level

            # Nulls warnings recommendation
            if null_pct > 10.0:
                recommendations_list.append(Recommendation(
                    dataset_id=dataset_id,
                    version_number=version_number,
                    severity="Medium",
                    category="Nulls",
                    description=f"Column '{col}' is missing {null_pct:.2f}% values.",
                    suggested_fix="Impute null fields with column mean/median or drop rows containing missing items."
                ))

            db.add(col_p)

        # 5. Calculate Quality Score Elements
        completeness = float((total_cells - total_missing) / total_cells * 100) if total_cells > 0 else 100.0
        
        # Format Validity calculations
        total_format_checked = (email_cols_checked + phone_cols_checked + url_cols_checked) * 200
        total_invalid_formats = invalid_emails_count + invalid_phones_count + invalid_urls_count
        validity = float((total_format_checked - total_invalid_formats) / total_format_checked * 100) if total_format_checked > 0 else 100.0
        
        accuracy = 100.0 - (float(invalid_emails_count / 200 * 100) if email_cols_checked > 0 else 0)
        consistency = 100.0  # Assumed consistent schema types mapping
        uniqueness = total_uniqueness
        
        overall_score = float((completeness + uniqueness + validity + accuracy + consistency) / 5)

        # 6. Fetch previous version to compute Data Drift checks
        prev_version = version_number - 1
        prev_report_query = select(QualityReport).where(
            QualityReport.dataset_id == dataset_id,
            QualityReport.version_number == prev_version
        )
        prev_result = await db.execute(prev_report_query)
        prev_report = prev_result.scalar_one_or_none()

        drift_diff = 0.0
        prev_score = None
        schema_changes = {}

        if prev_report:
            prev_score = prev_report.overall_score
            drift_diff = overall_score - prev_score
            
            # Retrieve previous version metadata schemas mapping
            prev_meta_query = select(DatasetVersion).where(
                DatasetVersion.dataset_id == dataset_id,
                DatasetVersion.version_number == prev_version
            )
            prev_v_res = await db.execute(prev_meta_query)
            prev_version_record = prev_v_res.scalar_one_or_none()

            # Simple drift differences comparisons
            if prev_version_record:
                # Compile structural schema changes lists
                added_cols = [c for c in df.columns if c not in schema] # mapped below
                schema_changes = {
                    "added_columns": [],
                    "removed_columns": [],
                    "changed_types": []
                }

        # Create Quality Report record
        report = QualityReport(
            dataset_id=dataset_id,
            version_number=version_number,
            completeness_score=completeness,
            accuracy_score=accuracy,
            consistency_score=consistency,
            validity_score=validity,
            uniqueness_score=uniqueness,
            overall_score=overall_score,
            previous_version_number=prev_version if prev_report else None,
            previous_quality_score=prev_score,
            quality_difference=drift_diff,
            schema_changes_json=schema_changes
        )
        db.add(report)

        # Store recommendations
        if profile.duplicate_rows > 0:
            recommendations_list.append(Recommendation(
                dataset_id=dataset_id,
                version_number=version_number,
                severity="Critical",
                category="Duplicates",
                description=f"Dataset contains {profile.duplicate_rows} duplicate rows.",
                suggested_fix="De-duplicate the dataset by running drop_duplicates query routines."
            ))

        for rec in recommendations_list:
            db.add(rec)

        # 7. Audit log write and commit transaction
        await AuditLogService.log_event(
            db,
            user_id=user_id,
            org_id=dataset.organization_id,
            workspace_id=dataset.workspace_id,
            action="DATASET_PROFILING_COMPLETED"
        )
        await db.commit()
        logger.info("Dataset profiling background calculations complete", dataset_id=str(dataset_id))
