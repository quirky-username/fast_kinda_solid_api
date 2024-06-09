import logging
from abc import ABCMeta
from enum import Enum, StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict
from structlog import getLogger

logger = getLogger(__name__)


class RepositorySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_REPOSITORY_",
    )

    PAGINATION_MAX: int = 1000
    SHOW_RECORDS_IN_LOGS: bool = False


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


class OpenTelemetrySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OTEL_",
    )

    ENABLE_CONSOLE_EXPORTER: bool = True
    ENABLE_OTEL_EXPORTER: bool = False
    OTLP_ENDPOINT: str | None = None
    INSECURE: bool = True
    HEADERS: dict | None = None
    TIMEOUT: int = 10
    AUTH_TOKEN: str | None = None
    OTLP_PROTOCOL: str = "grpc"


class BaseServiceSettings(BaseSettings, metaclass=ABCMeta):
    pass


class Environment(StrEnum):
    DEV = "DEV"
    TEST = "TEST"
    STAGING = "STAGING"
    PROD = "PROD"


__all__ = [
    "RepositorySettings",
    "ObservabilitySettings",
    "OpenTelemetrySettings",
    "BaseServiceSettings",
    "Environment",
]
