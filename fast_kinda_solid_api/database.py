from functools import cached_property
from typing import Set, Type

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.decl_api import registry

from fast_kinda_solid_api.config import SqlAlchemySettings
from fast_kinda_solid_api.domain.models import BaseTable


class Database:
    _registered_server_names: Set[str] = set()
    _registered_tables: Set[Type[BaseTable]] = set()

    def __init__(self, name: str, settings: SqlAlchemySettings, models: list[str]) -> None:
        self._register_name(name)
        self.settings = settings
        self.registry = registry()
        self._base: BaseTable | None = None
        self._models = models

    @cached_property
    def async_engine(self) -> AsyncEngine:
        return create_async_engine(
            self.settings.get_async_url(self.settings.DB),
            pool_pre_ping=self.settings.ENGINE_PRE_POOL_PING,
            echo=self.settings.ENGINE_ECHO_SQL,
        )

    @cached_property
    def session_maker(self) -> AsyncSession:
        return async_sessionmaker(
            bind=self.async_engine,
            expire_on_commit=self.settings.SESSION_EXPIRE_ON_COMMIT,
            class_=AsyncSession,
            autoflush=self.settings.SESSION_AUTO_FLUSH,
            future=self.settings.SESSION_FUTURE,
        )

    def import_models(self) -> None:
        for model in self._models:
            __import__(model)

    def get_declarative_base(self) -> DeclarativeBase:
        if self._base is None:
            self._base = self.registry.generate_base()

        return self._base

    def register_model(self, model: Type[BaseTable]) -> None:
        if model not in self._registered_tables:
            try:
                self.registry.map_declaratively(model)
            except Exception:
                pass

    def _register_name(self, name: str) -> None:
        if name in Database._registered_server_names:
            raise ValueError(f"BaseDatabase {name} is already registered.")

        Database._registered_server_names.add(name)
        self.name = name


async def get_current_transaction_id(session: AsyncSession):
    result = await session.execute("SELECT txid_current()")
    return result.scalar()


__all__ = [
    "Database",
    "get_current_transaction_id",
]
