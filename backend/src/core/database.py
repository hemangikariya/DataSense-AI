from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.config import settings
from src.core.logging import logger

# SQLAlchemy base model class
class Base(DeclarativeBase):
    pass

# Create async engine with production-ready connection pool parameters
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=30,
    max_overflow=15,
    pool_recycle=1800,
    pool_pre_ping=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection helper to yield transactional async database sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error("Database session transaction failed. Rolling back.", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """
    Validates PostgreSQL database connectivity by executing a raw query assertion.
    """
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error("PostgreSQL database connection health check failed", error=str(e))
        return False
