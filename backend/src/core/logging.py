import logging
import sys
import structlog
from src.config import settings


def configure_logging():
    logging_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Configure stdlib logging root handler
    logging.basicConfig(
        clean_format="%(message)s",
        stream=sys.stdout,
        level=logging_level,
    )

    # Configure structlog
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.ENV == "production":
        # JSON logs in production for ELK/Loki ingestion
        processors.append(structlog.processors.JSONRenderer())
    else:
        # ConsoleRenderer for local debugging readability
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("datasense")
