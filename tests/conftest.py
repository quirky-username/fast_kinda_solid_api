from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fast_kinda_solid_api.core.dependencies import get_async_session
from tests.fixtures.models import Base

DATABASE_URL = "postgresql+asyncpg://testuser:testpassword@localhost/testdb"

engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    async with get_async_session(async_session) as session:
        yield session
