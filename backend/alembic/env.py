import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import metadata and configuration settings
from src.config import settings
from src.core.database import Base
from src.modules.auth.models import User, RefreshToken, EmailVerificationToken, PasswordResetToken, Permission, Role, AuditLog
from src.modules.datasets.models import Dataset, DatasetVersion, DatasetMetadata, DatasetTag
from src.modules.profiling.models import DatasetProfile, ColumnProfile, QualityReport, Recommendation
from src.modules.dashboards.models import Dashboard, DashboardWidget, DashboardLayout, DashboardShare, DashboardFavorite
from src.modules.ai.models import Conversation, Message, AIRequest, AIResponse, PromptTemplate
from src.modules.analytics.models import Report, ReportSection, ScheduledReport, ReportHistory, PredictionJob, PredictionResult

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set up metadata targets
target_metadata = Base.metadata

# Inject database URL from pydantic settings dynamically
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
