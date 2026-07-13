import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # Security & Authentication
    SECRET_KEY: str = Field(default="devsecretkeydochangeinproduction!!!")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:securepass@localhost:5432/datasense")
    
    # Redis Cache & Broker
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # MinIO Storage
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadminpass")
    MINIO_SECURE: bool = Field(default=False)
    MINIO_BUCKET_NAME: str = Field(default="datasense-analytics")

    # AI API Keys
    GEMINI_API_KEY: str = Field(default="mock-gemini-key")

    # Observability
    SENTRY_DSN: Optional[str] = Field(default=None)
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = Field(default=None)


settings = Settings()
