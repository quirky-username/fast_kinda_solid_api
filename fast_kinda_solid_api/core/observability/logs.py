import contextvars
import logging
from enum import Enum

import structlog
from colorama import init as colorama_init
from pydantic_settings import BaseSettings, SettingsConfigDict
from pythonjsonlogger import jsonlogger

colorama_init(autoreset=True)


logger = structlog.getLogger("fast_kinda_solid_api")


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    FATAL = CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_OBSERVABILITY_",
    )
    LOG_LEVEL: LogLevel = LogLevel.DEBUG
    CONTEXT_VAR_PREFIX: str = "observability."
    CONSOLE_LOGGING: bool = True
    LOGGERS: list[str] = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "uvicorn.asgi",
        "sqlalchemy",
        "alembic",
        "fastapi",
        "opentelemetry",
        "asyncio",
    ]


def _add_observability_context(_, __, event_dict):
    """
    Processor to add contextvars from AsyncContextModel to the log.
    """
    for context_var, value in contextvars.copy_context().items():
        if context_var.name.startswith("observability"):
            key = context_var.name.lstrip("observability.")
            event_dict[f"{key}"] = value

    return event_dict


def configure_logging(settings: ObservabilitySettings):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_observability_context,
    ]

    if settings.CONSOLE_LOGGING:
        processors.extend([structlog.dev.set_exc_info, structlog.dev.ConsoleRenderer(colors=True)])
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler()
    if settings.CONSOLE_LOGGING:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev._format_exception,
            )
        )
        format = "%(message)s"
    else:
        formatter = jsonlogger.JsonFormatter()
        format = "%"

    handler.setFormatter(formatter)
    logging.basicConfig(
        format=format,
        handlers=[handler],
        level=settings.LOG_LEVEL.value,
    )


__all__ = [
    "ObservabilitySettings",
    "configure_logging",
]
