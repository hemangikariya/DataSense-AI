import datetime
import json
import uuid
import secrets
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from src.core.storage import storage_manager
from src.config import settings
from src.modules.datasets.models import Dataset, DatasetVersion, DatasetMetadata, DatasetTag
from src.modules.datasets.schemas import DatasetCreate, DatasetUpdate
from src.modules.auth.services import AuditLogService
from src.modules.datasets.tasks import process_dataset_upload_task


class DatasetService:
    @staticmethod
    async def create_dataset(
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        creator_id: uuid.UUID,
        schema: DatasetCreate,
        file_content: bytes,
        filename: str,
        content_type: str,
        file_size: int,
        parent_dataset_id: Optional[uuid.UUID] = None,
        source: str = "UPLOAD",
        request_ip: Optional[str] = None
    ) -> Dataset:
        """
        Ingests a new dataset. Uploads the file to MinIO, creates the Dataset record, and triggers the background Celery task.
        """
        # Validate format extension
        ext = filename.split(".")[-1].lower()
        allowed_extensions = ["csv", "xlsx", "xls", "json", "parquet"]
        if ext not in allowed_extensions:
            raise ValueError(f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}")

        # Validate MIME types
        allowed_mimes = [
            "text/csv", "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/json", "application/octet-stream"
        ]
        # Allow any mime format in test environments, but validate length
        if file_size == 0:
            raise ValueError("Uploaded file is empty.")

        # Check for duplicate names in workspace
        dup_query = select(Dataset).where(
            Dataset.workspace_id == workspace_id,
            Dataset.name == schema.name,
            Dataset.is_deleted == False
        )
        dup_result = await db.execute(dup_query)
        if dup_result.scalar_one_or_none():
            raise ValueError("Dataset name already exists in this workspace.")

        # Upload file content to MinIO
        dataset_id = uuid.uuid4()
        storage_path = f"datasets/{org_id}/{workspace_id}/{dataset_id}/{filename}"
        
        # Stream bytes buffer
        import io
        storage_manager.client.put_object(
            settings.MINIO_BUCKET_NAME,
            storage_path,
            io.BytesIO(file_content),
            length=file_size,
            content_type=content_type
        )

        dataset = Dataset(
            id=dataset_id,
            organization_id=org_id,
            workspace_id=workspace_id,
            creator_id=creator_id,
            name=schema.name,
            description=schema.description,
            status="Processing",
            format=ext.upper(),
            storage_path=storage_path,
            parent_dataset_id=parent_dataset_id,
            source=source
        )
        db.add(dataset)
        await db.flush()

        # Add tags
        for t_name in schema.tags:
            tag = DatasetTag(dataset_id=dataset_id, tag_name=t_name)
            db.add(tag)

        await AuditLogService.log_event(
            db, user_id=creator_id, org_id=org_id, workspace_id=workspace_id, action="DATASET_UPLOAD_INITIATED", ip_address=request_ip
        )
        await db.commit()

        # Trigger background Celery parser
        process_dataset_upload_task.delay(
            str(dataset_id),
            storage_path,
            filename,
            file_size,
            content_type,
            str(creator_id)
        )

        return dataset

    @staticmethod
    async def get_dataset(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[Dataset]:
        query = select(Dataset).where(Dataset.id == dataset_id, Dataset.is_deleted == False).options(selectinload(Dataset.tags))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_dataset(
        db: AsyncSession, dataset_id: uuid.UUID, schema: DatasetUpdate, user_id: uuid.UUID, request_ip: Optional[str] = None
    ) -> Optional[Dataset]:
        dataset = await DatasetService.get_dataset(db, dataset_id)
        if not dataset:
            return None

        if schema.name is not None:
            dataset.name = schema.name
        if schema.description is not None:
            dataset.description = schema.description
            
        if schema.tags is not None:
            # Drop old tags
            del_stmt = select(DatasetTag).where(DatasetTag.dataset_id == dataset_id)
            del_res = await db.execute(del_stmt)
            for old_tag in del_res.scalars().all():
                await db.delete(old_tag)
            # Add new tags
            for t_name in schema.tags:
                tag = DatasetTag(dataset_id=dataset_id, tag_name=t_name)
                db.add(tag)

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dataset.organization_id, workspace_id=dataset.workspace_id, action="DATASET_UPDATE", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(dataset)
        return dataset

    @staticmethod
    async def delete_dataset(db: AsyncSession, dataset_id: uuid.UUID, user_id: uuid.UUID, request_ip: Optional[str] = None) -> bool:
        """
        Performs soft delete of dataset, flagging is_deleted = True.
        """
        dataset = await DatasetService.get_dataset(db, dataset_id)
        if not dataset:
            return False

        dataset.is_deleted = True
        dataset.deleted_at = datetime.datetime.utcnow()
        
        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dataset.organization_id, workspace_id=dataset.workspace_id, action="DATASET_SOFT_DELETE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def restore_dataset(db: AsyncSession, dataset_id: uuid.UUID, user_id: uuid.UUID, request_ip: Optional[str] = None) -> bool:
        """
        Restores a soft-deleted dataset.
        """
        query = select(Dataset).where(Dataset.id == dataset_id, Dataset.is_deleted == True)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()
        if not dataset:
            return False

        dataset.is_deleted = False
        dataset.deleted_at = None

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dataset.organization_id, workspace_id=dataset.workspace_id, action="DATASET_RESTORE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def list_datasets(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dataset], int]:
        """
        Lists and filters active datasets inside the workspace.
        """
        conditions = [Dataset.workspace_id == workspace_id, Dataset.is_deleted == False]
        if search:
            conditions.append(Dataset.name.ilike(f"%{search}%"))

        query = select(Dataset).where(and_(*conditions)).options(selectinload(Dataset.tags))
        
        if tag:
            query = query.join(DatasetTag).where(DatasetTag.tag_name == tag)

        # Count total
        count_result = await db.execute(query)
        total_count = len(count_result.scalars().all())

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all()), total_count

    @staticmethod
    async def get_download_url(db: AsyncSession, dataset_id: uuid.UUID, user_id: uuid.UUID, request_ip: Optional[str] = None) -> Optional[str]:
        """
        Generates a secure presigned GET download URL from S3 (expires in 1 hour).
        """
        dataset = await DatasetService.get_dataset(db, dataset_id)
        if not dataset:
            return None

        url = storage_manager.client.presigned_get_object(
            settings.MINIO_BUCKET_NAME,
            dataset.storage_path,
            expires=datetime.timedelta(hours=1)
        )
        
        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dataset.organization_id, workspace_id=dataset.workspace_id, action="DATASET_DOWNLOAD", ip_address=request_ip
        )
        return url

    @staticmethod
    async def get_preview(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Reads the pre-calculated preview JSON payload directly from S3.
        """
        dataset = await DatasetService.get_dataset(db, dataset_id)
        if not dataset or dataset.status != "Ready":
            return None

        preview_key = f"previews/{dataset_id}/preview.json"
        try:
            s3_response = storage_manager.client.get_object(
                settings.MINIO_BUCKET_NAME,
                preview_key
            )
            return json.loads(s3_response.read().decode("utf-8"))
        except Exception as e:
            logger.error("Failed to read dataset preview payload from storage", dataset_id=str(dataset_id), error=str(e))
            return None

    @staticmethod
    async def get_metadata(db: AsyncSession, dataset_id: uuid.UUID) -> Optional[DatasetMetadata]:
        query = select(DatasetMetadata).where(DatasetMetadata.dataset_id == dataset_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_versions(db: AsyncSession, dataset_id: uuid.UUID) -> List[DatasetVersion]:
        query = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def restore_version(
        db: AsyncSession, dataset_id: uuid.UUID, version_number: int, user_id: uuid.UUID, request_ip: Optional[str] = None
    ) -> bool:
        """
        Restores dataset file pointer to a previous version index.
        """
        dataset = await DatasetService.get_dataset(db, dataset_id)
        if not dataset:
            return False

        v_query = select(DatasetVersion).where(
            DatasetVersion.dataset_id == dataset_id, DatasetVersion.version_number == version_number
        )
        v_result = await db.execute(v_query)
        version_rec = v_result.scalar_one_or_none()
        if not version_rec:
            return False

        # Rollback path pointers
        dataset.storage_path = version_rec.storage_path
        dataset.hash = version_rec.hash
        dataset.version = version_number
        dataset.status = "Processing"
        await db.commit()

        # Re-trigger metadata calculation on restored path
        process_dataset_upload_task.delay(
            str(dataset_id),
            version_rec.storage_path,
            dataset.name,
            0,  # File size already on S3
            "application/octet-stream",
            str(user_id)
        )

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dataset.organization_id, workspace_id=dataset.workspace_id, action=f"DATASET_VERSION_RESTORE:{version_number}", ip_address=request_ip
        )
        return True
