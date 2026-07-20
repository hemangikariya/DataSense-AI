from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from src.config import settings
from src.core.logging import configure_logging, logger
from src.core.cache import redis_manager
from src.core.storage import storage_manager
from src.core.database import check_db_health
from src.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from src.core.middleware import CorrelationAndLoggingMiddleware
from src.modules.auth.api import router as auth_router
from src.modules.organizations.api import router as org_router
from src.modules.datasets.api import router as dataset_router
from src.modules.profiling.api import router as profiling_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Events
    configure_logging()
    logger.info("Starting DataSense AI Backend application service...")
    
    # Initialize connection managers
    redis_manager.initialize()
    await redis_manager.ping()
    
    storage_manager.initialize()
    
    yield
    
    # Shutdown Events
    logger.info("Shutting down DataSense AI Backend application service...")
    await redis_manager.close()


app = FastAPI(
    title="DataSense AI",
    description="Enterprise AI Data Analyst & Business Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to NextJS route in production builds
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
app.add_middleware(CorrelationAndLoggingMiddleware)

# Global Exception overrides
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include modules routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(dataset_router, prefix="/api/v1")
app.include_router(profiling_router, prefix="/api/v1")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Checks"])
async def run_system_health_verification():
    """
    Consolidated health check validating Backend, Postgres, Redis, and MinIO.
    """
    db_ok = await check_db_health()
    redis_ok = await redis_manager.ping()
    minio_ok = storage_manager.check_health()
    
    healthy = db_ok and redis_ok and minio_ok
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if healthy else "degraded",
        "timestamp": app.openapi().get("info", {}).get("x-timestamp", None) or time_now(),
        "services": {
            "backend": "healthy",
            "postgres": "healthy" if db_ok else "unreachable",
            "redis": "healthy" if redis_ok else "unreachable",
            "minio": "healthy" if minio_ok else "unreachable"
        }
    }


def time_now() -> str:
    import datetime
    return datetime.datetime.utcnow().isoformat() + "Z"
