import logging
from enum import Enum

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


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
    model_config = ConfigDict(env_prefix="OBSERVABILITY_")

    CONTEXT_VAR_PREFIX: str = "observability."
    LOG_LEVEL: LogLevel = LogLevel.DEBUG
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


class OtelSettings(BaseSettings):
    model_config = ConfigDict(env_prefix="OTEL_")

    enable_console_exporter: bool = Field(default=False)
    enable_otel_exporter: bool = Field(default=False)
    otlp_endpoint: str | None = Field(None)
    insecure: bool = Field(default=True)
    headers: dict | None = Field(default=None)
    timeout: int | None = Field(default=10)
    auth_token: str | None = Field(default=None)
    otlp_protocol: str = Field(default="grpc")


__all__ = [
    "LogLevel",
    "ObservabilitySettings",
    "OtelSettings",
]
