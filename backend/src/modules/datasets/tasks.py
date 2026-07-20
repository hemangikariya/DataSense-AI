import asyncio
import io
import json
import hashlib
import uuid
import polars as pl
import pandas as pd
from typing import Dict, Any, Optional
from src.core.celery import celery_app
from src.core.database import AsyncSessionLocal
from src.core.storage import storage_manager
from src.core.logging import logger
from src.config import settings
from src.modules.datasets.models import Dataset, DatasetMetadata, DatasetVersion
from src.modules.auth.services import AuditLogService

# Helper to run async code inside Celery sync worker thread
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="datasets.process_upload")
def process_dataset_upload_task(
    dataset_id_str: str,
    storage_path: str,
    original_filename: str,
    file_size: int,
    content_type: str,
    user_id_str: Optional[str] = None
):
    """
    Celery task running asynchronously to calculate hash, parse files, profile schema, and build preview payloads.
    """
    logger.info("Starting background ingestion task for dataset", dataset_id=dataset_id_str)
    run_async(
        async_process_dataset(
            dataset_id=uuid.UUID(dataset_id_str),
            storage_path=storage_path,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            user_id=uuid.UUID(user_id_str) if user_id_str else None
        )
    )


async def async_process_dataset(
    dataset_id: uuid.UUID,
    storage_path: str,
    original_filename: str,
    file_size: int,
    content_type: str,
    user_id: Optional[uuid.UUID]
):
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch raw file from MinIO
            s3_response = storage_manager.client.get_object(
                settings.MINIO_BUCKET_NAME,
                storage_path
            )
            file_bytes = s3_response.read()
            
            # Calculate SHA256 checksum
            sha256_hash = hashlib.sha256(file_bytes).hexdigest()
            
            # 2. Check for duplicate upload hashes in the same workspace to prevent redundant ingest
            from sqlalchemy import select
            q = select(Dataset).where(Dataset.id == dataset_id)
            res = await db.execute(q)
            dataset = res.scalar_one()
            
            dup_query = select(Dataset).where(
                Dataset.workspace_id == dataset.workspace_id,
                Dataset.hash == sha256_hash,
                Dataset.id != dataset_id,
                Dataset.is_deleted == False
            )
            dup_result = await db.execute(dup_query)
            if dup_result.scalar_one_or_none():
                dataset.status = "Failed"
                dataset.description = "Duplicate upload check: Same file already exists in this workspace."
                await db.commit()
                logger.warn("Duplicate file hash check failed. Ingestion aborted.")
                return

            # 3. Parse bytes buffer based on format/extension
            buffer = io.BytesIO(file_bytes)
            ext = original_filename.split(".")[-1].lower()

            if ext == "csv":
                df = pl.read_csv(buffer)
            elif ext in ["xlsx", "xls"]:
                # Polars Excel reader requires openpyxl, pandas read is highly robust as fallback
                pandas_df = pd.read_excel(buffer)
                df = pl.from_pandas(pandas_df)
            elif ext == "parquet":
                df = pl.read_parquet(buffer)
            elif ext == "json":
                pandas_df = pd.read_json(buffer)
                df = pl.from_pandas(pandas_df)
            else:
                raise ValueError(f"Format extension .{ext} is unsupported.")

            # Validate empty file
            if df.height == 0:
                raise ValueError("File contains no row values.")

            # 4. Extract schema, rows, columns counts
            rows_count = df.height
            columns_count = df.width
            schema = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}

            # Generate summary statistics profile
            summary_stats = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                nulls = int(df[col].null_count())
                summary_stats[col] = {
                    "type": dtype,
                    "null_count": nulls,
                    "null_percentage": float(nulls / rows_count * 100) if rows_count > 0 else 0
                }
                
                # Check for numerical stats
                is_numeric = any(t in dtype for t in ["Int", "Float", "Decimal", "UInt"])
                if is_numeric:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    mean_val = df[col].mean()
                    summary_stats[col].update({
                        "min": float(min_val) if min_val is not None else None,
                        "max": float(max_val) if max_val is not None else None,
                        "mean": float(mean_val) if mean_val is not None else None,
                    })

            # Calculate duplicate rows
            duplicate_rows_count = int(rows_count - df.unique().height)

            # 5. Build first 100 rows preview payload
            preview_df = df.head(100)
            preview_list = []
            
            # Serialize cells cleanly
            for row in preview_df.to_dicts():
                clean_row = {}
                for k, v in row.items():
                    if isinstance(v, (datetime.datetime, datetime.date)):
                        clean_row[k] = v.isoformat()
                    else:
                        clean_row[k] = v
                preview_list.append(clean_row)

            preview_data = {
                "columns": df.columns,
                "datatypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
                "missing_values": {col: int(df[col].null_count()) for col in df.columns},
                "duplicate_rows": duplicate_rows_count,
                "row_count": rows_count,
                "preview_data": preview_list
            }

            # 6. Save Preview JSON file to S3 storage bucket
            preview_key = f"previews/{dataset_id}/preview.json"
            preview_bytes = json.dumps(preview_data).encode("utf-8")
            storage_manager.client.put_object(
                settings.MINIO_BUCKET_NAME,
                preview_key,
                io.BytesIO(preview_bytes),
                length=len(preview_bytes),
                content_type="application/json"
            )

            # 7. Create Metadata Profile and Version records
            metadata = DatasetMetadata(
                dataset_id=dataset_id,
                original_filename=original_filename,
                file_size=file_size,
                file_type=content_type,
                rows_count=rows_count,
                columns_count=columns_count,
                schema_json=schema,
                summary_stats_json=summary_stats
            )
            db.add(metadata)

            version = DatasetVersion(
                dataset_id=dataset_id,
                version_number=1,
                storage_path=storage_path,
                hash=sha256_hash,
                change_log="Original dataset file ingestion."
            )
            db.add(version)

            # Update Dataset state
            dataset.status = "Ready"
            dataset.hash = sha256_hash
            
            # Log successful audit
            await AuditLogService.log_event(
                db,
                user_id=user_id,
                org_id=dataset.organization_id,
                workspace_id=dataset.workspace_id,
                action="DATASET_INGEST_SUCCESS"
            )
            await db.commit()
            logger.info("Dataset background processing completed successfully", dataset_id=str(dataset_id))

        except Exception as e:
            logger.error("Dataset ingestion pipeline failed", dataset_id=str(dataset_id), error=str(e))
            # Set failed status in database
            dataset.status = "Failed"
            dataset.description = f"Ingestion failed: {str(e)}"
            await AuditLogService.log_event(
                db,
                user_id=user_id,
                org_id=dataset.organization_id,
                workspace_id=dataset.workspace_id,
                action="DATASET_INGEST_FAILED"
            )
            await db.commit()
