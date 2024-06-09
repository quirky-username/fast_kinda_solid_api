import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fast_kinda_solid_api.core.layers.repository import NotFoundError
from fast_kinda_solid_api.core.settings import RepositorySettings
from tests.fixtures.dtos import KeysetPaginatableCreate, KeysetPaginatableUpdate
from tests.fixtures.repositories import PaginationRepository


@pytest.mark.asyncio
async def test_create_record(async_db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(async_db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    assert record.name == "Test Item"
    assert record.id is not None
    assert record.created_at is not None


@pytest.mark.asyncio
async def test_update_record(async_db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(async_db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    update_dto = KeysetPaginatableUpdate(id=record.id, name="Updated Item", order=2)
    await repo.update_one(update_dto)

    updated_record = await repo.lookup(update_dto.id)

    assert updated_record.id == record.id
    assert updated_record.created_at == record.created_at
    assert updated_record.name == update_dto.name
    assert updated_record.order == update_dto.order


@pytest.mark.asyncio
async def test_soft_delete_record(async_db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(async_db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    await repo.delete_one(record.id, soft_delete=True)

    with pytest.raises(NotFoundError):
        await repo.lookup(record.id)


@pytest.mark.asyncio
async def test_delete_record(async_db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(async_db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    await repo.delete_one(record.id, soft_delete=False)

    with pytest.raises(NotFoundError):
        await repo.lookup(record.id)


@pytest.mark.asyncio
async def test_lookup_record(async_db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(async_db_session, settings)

    create_dto = KeysetPaginatableCreate(name="Test Item", order=1)
    record = await repo.create_one(create_dto)

    found_record = await repo.lookup(record.id)
    assert found_record.name == "Test Item"
    assert found_record.id == record.id


@pytest.mark.asyncio
async def test_list_paginated(async_db_session: AsyncSession) -> None:
    settings = RepositorySettings(PAGINATION_MAX=10)
    repo = PaginationRepository(async_db_session, settings)

    async with repo.async_nested_transaction():
        # Create sample data
        for i in range(10):
            create_dto = KeysetPaginatableCreate(name=f"Item {i}", order=i)
            await repo.create_one(create_dto)

    # Test pagination
    record_set = await repo.query(sort_field="order", unique_field="id", page_size=5)
    first_page = record_set.records
    assert len(first_page) == 5
    assert first_page[0].name == "Item 0"
    assert first_page[-1].name == "Item 4"

    last_sort_value = first_page[-1].order
    last_unique_value = first_page[-1].id
    record_set = await repo.query(
        sort_field="order",
        unique_field="id",
        last_sort_value=last_sort_value,
        last_unique_value=last_unique_value,
        page_size=5,
    )
    second_page = record_set.records
    assert len(second_page) == 5
    assert second_page[0].name == "Item 5"
    assert second_page[-1].name == "Item 9"

    # Test that no more records exist beyond the second page
    last_sort_value = second_page[-1].order
    last_unique_value = second_page[-1].id
    record_set = await repo.query(
        sort_field="order",
        unique_field="id",
        last_sort_value=last_sort_value,
        last_unique_value=last_unique_value,
        page_size=5,
    )
    assert len(record_set.records) == 0
