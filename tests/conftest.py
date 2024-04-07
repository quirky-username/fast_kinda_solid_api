from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from fast_kinda_solid_api.core.dependencies import (
    AsyncSqlAlchemySession,
    SqlAlchemySettings,
)
from tests.fixtures.models import Base

db_settings = SqlAlchemySettings(
    NAME="testdb",
    HOST="localhost",
    USER="testuser",
    PASSWORD_SECRET_NAME="pass",  # not used in testing
    PORT=5432,
    ECHO=True,
    POOL_SIZE=10,
    MAX_OVERFLOW=20,
)

sqlalchemy_session = AsyncSqlAlchemySession(
    db_settings, "testpassword"
)  # hard coded password instead of using secrets manager


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[None, None]:
    await sqlalchemy_session.startup_all()

    async with sqlalchemy_session.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with sqlalchemy_session.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    async with sqlalchemy_session() as async_session:
        yield async_session
