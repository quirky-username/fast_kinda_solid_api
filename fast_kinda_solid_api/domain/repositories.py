from abc import ABC
from typing import Any, Generic, Type, TypeVar

from fastapi.concurrency import asynccontextmanager
from sqlalchemy import delete, func, inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from fast_kinda_solid_api.config import RepositorySettings
from fast_kinda_solid_api.contexts import RepositoryOperationContext
from fast_kinda_solid_api.observability.logs import logger
from fast_kinda_solid_api.observability.tracing import span_function
from fast_kinda_solid_api.utils.sqla_helpers.query import select_with_cursor_pagination

from .dto import BaseDTO, BaseRecordDTO, BaseUpdateDTO
from .models import BaseTable

TCreate = TypeVar("TCreate", bound=BaseDTO)
TUpdate = TypeVar("TUpdate", bound=BaseUpdateDTO)
TRecord = TypeVar("TRecord", bound=BaseRecordDTO)


class NotFoundError(Exception):
    def __init__(self, model_name: str, identifier: str) -> None:
        self.model_name = model_name
        self.identifier = identifier

        message = f"{model_name} with id {identifier} not found in database"
        super().__init__(message)


_validated_indexes: dict = {}


class RepositoryMixin(Generic[TCreate, TUpdate, TRecord], ABC):
    __model_cls__: Type[BaseTable]
    __record_cls__: Type[TRecord]

    def __init__(self, db_session: AsyncSession, settings: RepositorySettings):
        if not hasattr(self, "__model_cls__"):
            raise TypeError(f"{self.__class__.__name__} does not define the attribute 'model_cls'")

        if not hasattr(self, "__record_cls__"):
            raise TypeError(f"{self.__class__.__name__} does not define the attribute '__record_cls__'")

        self.db_session = db_session
        self.settings = settings

    async def commit(self):
        await self.db_session.commit()
        logger.debug("Committed transaction manually")

    @asynccontextmanager
    async def async_nested_transaction(self):
        async with self.db_session.begin_nested() as nested_transaction:
            logger.debug("Nested transaction begin")
            try:
                yield nested_transaction
                logger.debug("Nested transaction body complete")
                await nested_transaction.commit()
                logger.debug("Nested transaction committed")
            except Exception as e:
                await nested_transaction.rollback()
                logger.error("Nested transaction error", exc_info=e)
                raise e

        logger.debug("Nested transaction end")

    async def create_one(self, obj: TCreate) -> TRecord:
        results: list[TRecord] = await self.bulk_create([obj])
        return results[0]

    @span_function("bulk_create")
    async def bulk_create(self, objects: list[TCreate]) -> list[TRecord]:
        models = [self.__model_cls__.convert_from(dto) for dto in objects]

        try:
            async with self.async_nested_transaction():
                for model in models:
                    self.db_session.add(model)

            logger.debug(f"Added {len(models)} instances to nested transaction")
        except IntegrityError as e:
            logger.error(
                f"Failed to map from dto {objects[0].__class__.__qualname__} to model {self.__model_cls__.__qualname__}"
            )
            if self.settings.SHOW_RECORDS_IN_LOGS:
                logger.error(e)

            raise

        for model in models:
            logger.debug(f"Added {self.__model_cls__.__name__}(id:{model.id}) on the transaction")

        logger.info(f"Added {len(models)} {self.__model_cls__.__name__} instances on the transaction")

        return [self.__record_cls__.convert_from(model) for model in models]

    @span_function("update_one")
    async def update_one(self, obj: TUpdate):
        # TODO: setup a NOT_SET sentinel value for fields that should not be updated
        async with RepositoryOperationContext.bind(
            model_id=obj.id,
            model_class=self.__model_cls__.__qualname__,
            input_dto_class=obj.__class__.__qualname__,
            output_dto_class=self.__record_cls__.__qualname__,
        ):
            update_mapping = obj.to_dict()

            stmt = (
                update(self.__model_cls__)
                .where(self.__model_cls__.id == obj.id)
                .values(**update_mapping)
                .execution_options(synchronize_session="fetch")
            )

            await self.db_session.execute(stmt)
            logger.info("Updated model instance on the session transaction")

    @span_function("bulk_update")
    async def bulk_update(self, objects: list[TUpdate]):
        update_mappings = [obj.to_dict() for obj in objects]

        await self.db_session.execute(update(self.__model_cls__), update_mappings)
        for obj in objects:
            logger.debug("Updated model instance on the session transaction")

        logger.info(f"Updated {len(objects)} {self.__model_cls__.__name__} instances on the transaction")

    async def delete_one(self, record_id: str, soft_delete: bool = True):
        await self.bulk_delete([record_id], soft_delete)

    @span_function("bulk_delete")
    async def bulk_delete(self, record_ids: list[str], soft_delete: bool = True):
        if soft_delete:
            stmt = update(self.__model_cls__).where(self.__model_cls__.id.in_(record_ids)).values(deleted_at=func.now())

            await self.db_session.execute(stmt)

            for record_id in record_ids:
                logger.debug(f"Soft deleted {self.__model_cls__.__name__}(id: {record_id}) on the transaction")

            logger.info(f"Soft deleted {len(record_ids)} {self.__model_cls__.__name__} instances on the transaction")
        else:
            stmt = delete(self.__model_cls__).where(self.__model_cls__.id.in_(record_ids))
            await self.db_session.execute(stmt)

            for record_id in record_ids:
                logger.debug(f"Hard deleted {self.__model_cls__.__name__}(id: {record_id}) on the transaction")

            logger.info(f"Hard deleted {len(record_ids)} {self.__model_cls__.__name__} instances on the transaction")

    @span_function("lookup")
    async def lookup(self, record_id: str, respect_soft_delete: bool = True) -> TRecord:
        stmt = select(self.__model_cls__).filter_by(id=record_id)
        result = await self.db_session.execute(stmt)
        model: BaseTable = result.scalar_one_or_none()

        if model is None:
            logger.info(f"Not Found {self.__model_cls__.__name__}(id: {record_id}) on the database")
            raise NotFoundError(self.__model_cls__.__name__, record_id)

        is_soft_deleted = respect_soft_delete and model.deleted_at is not None
        if is_soft_deleted:
            logger.debug(f"Ignoring soft deleted record {self.__model_cls__.__name__}(id: {record_id})")
            raise NotFoundError(self.__model_cls__.__name__, record_id)

        logger.info(f"Found {self.__model_cls__.__name__}(id: {record_id}) on the database")

        record: TRecord = self.__record_cls__.convert_from(model)
        return record

    @span_function("bulk_lookup")
    async def bulk_lookup(self, record_ids: list[str], respect_soft_delete: bool = True) -> list[TRecord]:
        stmt = select(self.__model_cls__).where(self.__model_cls__.id.in_(record_ids))

        if respect_soft_delete:
            stmt = stmt.where(self.__model_cls__.deleted_at is None)

        result = await self.db_session.execute(stmt)
        records: list[TRecord] = result.scalars().all()

        logger.info(f"Found {len(records)} {self.__model_cls__.__name__} records on the database")
        return records

    @span_function("list")
    async def list(
        self,
        sort_field: str,
        unique_field: str,
        last_sort_value: Any = None,
        last_unique_value: Any = None,
        ascending: bool = True,
        page_size: int = 10,
        respect_soft_delete: bool = True,
    ) -> list[TRecord]:
        if page_size > self.settings.PAGINATION_MAX:
            raise ValueError(f"Cannot paginate with a page_size greater than {self.settings.PAGINATION_MAX}")

        self._verify_composite_index_exists(sort_field, unique_field)

        base_stmt = select(self.__model_cls__)

        if respect_soft_delete:
            base_stmt = base_stmt.where(self.__model_cls__.deleted_at.is_(None))

        sort_col = getattr(self.__model_cls__, sort_field)
        unique_col = getattr(self.__model_cls__, unique_field)
        stmt = select_with_cursor_pagination(
            base_stmt,
            sort_col=sort_col,
            unique_col=unique_col,
            last_sort_value=last_sort_value,
            last_unique_value=last_unique_value,
            ascending=ascending,
            page_size=page_size,
        )

        result = await self.db_session.execute(stmt)
        results = result.fetchall()
        records: list[TRecord] = [
            self.__record_cls__.from_dict(self.__model_cls__(**row._asdict()).to_dict()) for row in results
        ]

        logger.info(f"Listed {len(records)} {self.__model_cls__.__name__} instances")
        return records

    def _verify_composite_index_exists(self, sort_column: str, unique_field: str) -> None:
        key = (self.__model_cls__, sort_column, unique_field)

        if key not in _validated_indexes:
            index_exists = _composite_index_exists(self.__model_cls__, sort_column, unique_field)
            if not index_exists:
                raise ValueError(f"No index found {self.__model_cls__.__name__}({sort_column}, {unique_field})")

            _validated_indexes[key] = index_exists
            logger.debug(f"Updated index cache {self.__model_cls__.__name__}({sort_column}, {unique_field})")

        logger.debug(f"Verified index exists {self.__model_cls__.__name__}({sort_column}, {unique_field})")


def _composite_index_exists(model: Type[DeclarativeBase], column1: str, column2: str) -> bool:
    inspector = inspect(model.__table__)
    for index in inspector.indexes:
        columns = index.columns.keys()
        if column1 in columns and column2 in columns:
            return True
    return False


__all__ = [
    "NotFoundError",
    "RepositoryMixin",
]
