import uuid

from fastapi.concurrency import asynccontextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from structlog import getLogger

from fast_kinda_solid_api.core.dependency_provider import DependencyProvider
from fast_kinda_solid_api.core.observability.context import RequestContext

logger = getLogger(__name__)


class SqlAlchemySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
    )

    NAME: str
    HOST: str
    USER: str
    PASSWORD_SECRET_NAME: str
    PORT: int = 5432
    ECHO: bool = False
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20


class AsyncSqlAlchemySession(DependencyProvider):
    engine: AsyncEngine
    async_sessio_nmaker: async_sessionmaker[AsyncSession]
    settings: SqlAlchemySettings

    def __init__(self, settings: SqlAlchemySettings, db_password: str) -> None:
        self.settings = settings
        self._db_password = db_password

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.settings.USER}:{self._db_password}@{self.settings.HOST}:{self.settings.PORT}/{self.settings.NAME}"  # noqa E501

    async def startup(self):
        self.engine = create_async_engine(
            self.db_url,
            echo=self.settings.ECHO,
            pool_size=self.settings.POOL_SIZE,
            max_overflow=self.settings.MAX_OVERFLOW,
        )

        self.async_session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def shutdown(self):
        await self.engine.dispose()

    @asynccontextmanager
    async def provide(self):
        logger.debug("Starting a new database session")

        async with self.async_session_maker() as session:
            async with session.begin():
                async with RequestContext.bind(session_id=str(uuid.uuid4())):
                    logger.debug("Session started")

                    transaction_id, connection_id = await self._get_session_meta(session)
                    async with RequestContext.bind(
                        transaction_id=str(transaction_id), connection_id=str(connection_id)
                    ):
                        logger.debug("Session started")

                        try:
                            yield session
                        except Exception as e:
                            logger.error("An error occurred during the session. Rolling back.", exc_info=True)
                            await session.rollback()
                            raise e

                        logger.debug("Session closing")

    async def _get_session_meta(self, session):
        query = select(func.txid_current(), func.pg_backend_pid())
        result = await session.execute(query)
        row = result.one()
        return row.txid_current, row.pg_backend_pid


__all__ = [
    "AsyncSqlAlchemySession",
    "SqlAlchemySettings",
]
