from abc import ABCMeta

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

from fast_kinda_solid_api.observability.config import (
    ObservabilitySettings,
    OtelSettings,
)


class SqlAlchemySettings(BaseSettings):
    model_config = ConfigDict(env_prefix="SQLA_")

    DB: str
    ADMIN_DB: str
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str

    ASYNC_DIALECT: str
    ASYNC_DRIVER: str | None
    SYNC_DIALECT: str
    SYNC_DRIVER: str | None = None

    ENGINE_PRE_POOL_PING: bool = True
    ENGINE_ECHO_SQL: bool = True

    SESSION_EXPIRE_ON_COMMIT: bool = False
    SESSION_AUTO_FLUSH: bool = False
    SESSION_FUTURE: bool = True

    def get_async_url(self, db: str) -> str:
        if self.ASYNC_DRIVER:
            protocol = f"{self.ASYNC_DIALECT}+{self.ASYNC_DRIVER}"
        else:
            protocol = self.ASYNC_DIALECT
        return f"{protocol}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{db}"

    def get_sync_url(self, db: str) -> str:
        if self.SYNC_DRIVER:
            protocol = f"{self.SYNC_DIALECT}+{self.SYNC_DRIVER}"
        else:
            protocol = self.SYNC_DIALECT
        return f"{protocol}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{db}"


class RepositorySettings(BaseSettings):
    model_config = ConfigDict(env_prefix="REPO_")

    PAGINATION_MAX: int = 10000
    SHOW_RECORDS_IN_LOGS: bool = False


class ServerSettings(BaseSettings):
    model_config = ConfigDict(env_prefix="SERVER_")

    HOST: str = "0.0.0.0"
    PORT: int = 5198
    RELOAD: bool = False
    ENABLE_TRACEBACK: bool = True
    OTEL_SETTINGS: OtelSettings = OtelSettings()
    OBSERVABILITY_SETTINGS: ObservabilitySettings = ObservabilitySettings()


class Environment(BaseSettings):
    model_config = ConfigDict(env_prefix="ENV_")

    DEV: str = "DEV"
    TEST: str = "TEST"
    STAGING: str = "STAGING"
    PROD: str = "PROD"

    CURRENT: str = "DEV"


class BaseServiceSettings(BaseSettings, metaclass=ABCMeta):
    pass


class BaseApiSettings(BaseSettings):
    ENV: Environment = Environment(CURRENT="DEV")
    SERVER: ServerSettings = ServerSettings()
    REPO: RepositorySettings = RepositorySettings()
    SQLALCHEMY: SqlAlchemySettings | None = None


__all__ = [
    "BaseApiSettings",
    "BaseServiceSettings",
    "Environment",
    "RepositorySettings",
    "ServerSettings",
    "SqlAlchemySettings",
]
