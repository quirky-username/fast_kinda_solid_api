import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_kinda_solid_api.config import RepositorySettings
from fast_kinda_solid_api.database import Database
from fast_kinda_solid_api.domain.repositories import NotFoundError
from tests.fixtures.models import KeysetPaginatableObject
from tests.fixtures.repositories import PaginationRepository
from tests.fixtures.schemas import KeysetPaginatableCreate, KeysetPaginatableUpdate


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session(setup_test_db: Database):
    async with setup_test_db.async_engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")
            yield session
            await transaction.rollback()


async def test_create_record(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    assert record.name == "Test Item"
    assert record.id is not None
    assert record.created_at is not None


async def test_update_record(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    update_dto = KeysetPaginatableUpdate(id=record.id, name="Updated Item", order=2)
    await repo.update_one(update_dto)

    updated_record = await repo.lookup(update_dto.id)

    assert updated_record.id == record.id
    assert updated_record.created_at == record.created_at
    assert updated_record.name == update_dto.name
    assert updated_record.order == update_dto.order


async def test_delete_record(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    await repo.delete_one(record.id, soft_delete=False)

    with pytest.raises(NotFoundError):
        await repo.lookup(record.id)


async def test_soft_delete_record(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    await repo.delete_one(record.id, soft_delete=True)

    with pytest.raises(NotFoundError):
        await repo.lookup(record.id)


async def test_lookup_record(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    found_record = await repo.lookup(record.id)
    assert found_record.name == "Test Item"
    assert found_record.id == record.id


async def test_list_paginated(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    # Create sample data
    for i in range(10):
        create_dto = KeysetPaginatableCreate(name=f"Item {i}", order=i)
        await repo.create_one(create_dto)

    await db_session.commit()

    # Test pagination
    first_page = await repo.list(sort_field="order", unique_field="id", page_size=5)
    assert len(first_page) == 5
    assert first_page[0].name == "Item 0"
    assert first_page[-1].name == "Item 4"

    last_sort_value = first_page[-1].order
    last_unique_value = first_page[-1].id
    second_page = await repo.list(
        sort_field="order",
        unique_field="id",
        last_sort_value=last_sort_value,
        last_unique_value=last_unique_value,
        page_size=5,
    )
    assert len(second_page) == 5
    assert second_page[0].name == "Item 5"
    assert second_page[-1].name == "Item 9"

    # Test that no more records exist beyond the second page
    last_sort_value = second_page[-1].order
    last_unique_value = second_page[-1].id
    empty_page = await repo.list(
        sort_field="order",
        unique_field="id",
        last_sort_value=last_sort_value,
        last_unique_value=last_unique_value,
        page_size=5,
    )
    assert len(empty_page) == 0


async def test_paginate_records_respects_soft_deletes(db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(db_session, settings)

    # Create sample data
    for i in range(10):
        create_dto = KeysetPaginatableCreate(name=f"Item {i}", order=i)
        await repo.create_one(create_dto)

    await db_session.commit()

    stmt = select(KeysetPaginatableObject).where(KeysetPaginatableObject.name == "Item 1")
    result = await db_session.execute(stmt)
    delete_record = result.scalars().first()

    await repo.delete_one(delete_record.id, soft_delete=True)
    await db_session.commit()

    # Test pagination
    first_page = await repo.list(sort_field="order", unique_field="id", page_size=5)
    assert len(first_page) == 5
    assert first_page[0].name == "Item 0"
    assert first_page[1].name == "Item 2"
    assert first_page[2].name == "Item 3"
    assert first_page[3].name == "Item 4"
    assert first_page[4].name == "Item 5"
