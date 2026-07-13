from minio import Minio
from src.config import settings
from src.core.logging import logger


class MinioStorageManager:
    def __init__(self):
        self.client: Minio = None

    def initialize(self):
        """
        Creates and validates MinIO client connection parameters, and ensures target buckets are created.
        """
        logger.info("Initializing MinIO connection manager...", endpoint=settings.MINIO_ENDPOINT)
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )

            # Assert standard storage buckets exist
            bucket = settings.MINIO_BUCKET_NAME
            if not self.client.bucket_exists(bucket):
                logger.info("MinIO bucket does not exist. Creating bucket...", bucket=bucket)
                self.client.make_bucket(bucket)
        except Exception as e:
            logger.error("MinIO storage manager failed to initialize", error=str(e))
            raise

    def check_health(self) -> bool:
        """
        Verifies client communication by listing configured S3 storage buckets.
        """
        if not self.client:
            return False
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            logger.error("MinIO object storage connection health check failed", error=str(e))
            return False


storage_manager = MinioStorageManager()
