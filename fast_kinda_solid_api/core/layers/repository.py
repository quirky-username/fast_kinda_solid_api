from abc import ABC
from typing import Any, Generic, Type, TypeVar

from fastapi.concurrency import asynccontextmanager
from sqlalchemy import (
    Column,
    Select,
    and_,
    asc,
    delete,
    desc,
    func,
    inspect,
    or_,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from structlog import get_logger

from fast_kinda_solid_api.core.data.convertible import ConvertibleBaseModel
from fast_kinda_solid_api.core.data.dto import (
    BaseRecord,
    BaseRecordReference,
    BooleanExpression,
    BooleanOperator,
    CursorPagination,
    Operation,
    Operator,
    RecordSet,
)
from fast_kinda_solid_api.core.data.model import DbModel, DbRecord
from fast_kinda_solid_api.core.observability.context import RepositoryOperationContext
from fast_kinda_solid_api.core.observability.tracing import span_function
from fast_kinda_solid_api.core.settings import RepositorySettings

logger = get_logger(__name__)

TCreate = TypeVar("TCreate", bound=ConvertibleBaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseRecordReference)
TRecord = TypeVar("TRecord", bound=BaseRecord)


class NotFoundError(Exception):
    def __init__(self, model_name: str, identifier: str) -> None:
        self.model_name = model_name
        self.identifier = identifier

        message = f"{model_name} with id {identifier} not found in database"
        super().__init__(message)


_validated_indexes: dict = {}


class BaseRepository(Generic[TRecord], ABC):
    """
    A base class that provides common CRUD operations for a repository.

    Generics:
        TRecord (BaseRecordDTO): The DTO class that is returned in responses

    Attributes:
        __model_cls__ (Type[DbModel]): The SQLAlchemy model class that the repository operates on.
        __record_cls__ (Type[TRecord]): The DTO class that the repository returns in responses.
    """

    __model_cls__: Type[DbRecord]
    __record_cls__: Type[TRecord]

    def __init__(self, db_session: AsyncSession, settings: RepositorySettings):
        if not hasattr(self, "__model_cls__"):
            raise TypeError(f"{self.__class__.__name__} does not define the attribute 'model_cls'")

        if not hasattr(self, "__record_cls__"):
            raise TypeError(f"{self.__class__.__name__} does not define the attribute '__record_cls__'")

        self.db_session = db_session
        self.settings = settings

    async def commit(self):
        """
        Commit the current transaction to the database.
        """
        await self.db_session.commit()
        logger.debug("Committed transaction to the database")

    async def refresh(self, model: DbModel):
        """
        Refresh the model attributes from the database.
        """
        await self.db_session.refresh(model)
        logger.debug(f"Refreshed {self.__model_cls__.__name__} from the database")

    @asynccontextmanager
    async def async_nested_transaction(self):
        """
        Create a nested transaction context manager.

        Yields:
            AsyncSession: The nested transaction session.
        """

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

    async def create_one(self, obj: BaseRecordReference) -> TRecord:
        results: list[TRecord] = await self.bulk_create([obj])
        return results[0]

    @span_function("bulk_create")
    async def bulk_create(self, objects: list[BaseRecordReference]) -> list[TRecord]:
        """
        Create multiple records in the database.

        Arguments:
            objects (list[BaseRecordDTO]): The DTOs to create.
        """
        models = [self.__model_cls__.convert_from(obj) for obj in objects]

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
    async def update_one(self, obj: BaseRecordReference, exclude_unset: bool = True):
        """
        Update a record in the database.

        Arguments:
            obj (BaseRecordDTO): The DTO to update.
            exclude_unset (bool): Whether to exclude unset values from the update.
        """
        # TODO: setup a NOT_SET sentinel value for fields that should not be updated
        async with RepositoryOperationContext.bind(
            model_id=obj.id,
            model_class=self.__model_cls__.__qualname__,
            input_dto_class=obj.__class__.__qualname__,
            output_dto_class=self.__record_cls__.__qualname__,
        ):
            update_mapping = obj.to_dict(exclude_unset=exclude_unset)

            stmt = (
                update(self.__model_cls__)
                .where(self.__model_cls__.id == obj.id)
                .values(**update_mapping)
                .execution_options(synchronize_session="fetch")
            )

            await self.db_session.execute(stmt)
            logger.info("Updated model instance on the session transaction")

    @span_function("bulk_update")
    async def bulk_update(self, objects: list[BaseRecordReference], exclude_unset: bool = True):
        """
        Update multiple records in the database.

        Arguments:
            objects (list[BaseRecordDTO]): The DTOs to update.
            exclude_unset (bool): Whether to exclude unset values from the update.
        """
        update_mappings = [obj.to_dict(exclude_unset=exclude_unset) for obj in objects]

        await self.db_session.execute(update(self.__model_cls__), update_mappings)
        for obj in objects:
            logger.debug("Updated model instance on the session transaction")

        logger.info(f"Updated {len(objects)} {self.__model_cls__.__name__} instances on the transaction")

    async def delete_one(self, record_id: str, soft_delete: bool = True):
        await self.bulk_delete([record_id], soft_delete)

    @span_function("bulk_delete")
    async def bulk_delete(self, record_ids: list[str], soft_delete: bool = True):
        """
        Delete multiple records from the database by their IDs.

        Arguments:
            record_ids (list[str]): The IDs of the records to delete.
            soft_delete (bool): Whether to soft delete the records.
        """
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
        """
        Lookup a record from the database by its ID.

        Arguments:
            record_id (str): The ID of the record to lookup.
            respect_soft_delete (bool): Whether to respect the soft delete flag.
        """
        stmt = select(self.__model_cls__).filter_by(id=record_id)
        result = await self.db_session.execute(stmt)
        model: DbRecord | None = result.scalar_one_or_none()

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
        """
        Lookup multiple records from the database by their IDs.

        Arguments:
            record_ids (list[str]): The IDs of the records to lookup.
            respect_soft_delete (bool): Whether to respect the soft delete flag.
        """
        stmt = select(self.__model_cls__).where(self.__model_cls__.id.in_(record_ids))

        if respect_soft_delete:
            stmt = stmt.where(self.__model_cls__.deleted_at is None)

        result = await self.db_session.execute(stmt)
        records: list[TRecord] = result.scalars().all()

        logger.info(f"Found {len(records)} {self.__model_cls__.__name__} records on the database")
        return records

    async def _query(
        self,
        filter: Operation | BooleanExpression,
    ):
        stmt = select(self.__model_cls__).filter(filter.to_sql(self.__model_cls__))
        result = await self.db_session.execute(stmt)
        return result.scalars

    @span_function("query")
    async def query(
        self,
        sort_field: str = "created_at",
        unique_field: str = "id",
        last_sort_value: Any = None,
        last_unique_value: Any = None,
        ascending: bool = True,
        page_size: int = 10,
        filter: Operation | BooleanExpression | None = None,
        respect_soft_delete: bool = True,
    ) -> RecordSet[TRecord]:
        """
        Query records from the database, paginated by a sort field and a unique field.

        Arguments:
            sort_field (str): The field to sort the records by.
            unique_field (str): The field to use as a tiebreaker for sorting.
            last_sort_value (Any): The last value of the sort field from the previous page.
            last_unique_value (Any): The last value of the unique field from the previous page.
            ascending (bool): Whether to sort the records in ascending order.
            page_size (int): The number of records to return per page.
            filter (Operation | BooleanExpression): The filter to apply to the query
            respect_soft_delete (bool): Whether to respect the soft delete flag.

        Returns:
            RecordSet: A set of records and pagination information.
        """
        if page_size > self.settings.PAGINATION_MAX:
            raise ValueError(f"Cannot paginate with a page_size greater than {self.settings.PAGINATION_MAX}")

        self._verify_composite_index_exists(sort_field, unique_field)

        base_stmt = select(self.__model_cls__)

        if filter:
            base_stmt = base_stmt.where(self._build_filter(filter))

        if respect_soft_delete:
            base_stmt = base_stmt.where(self.__model_cls__.deleted_at.is_(None))

        sort_col = getattr(self.__model_cls__, sort_field)
        unique_col = getattr(self.__model_cls__, unique_field)
        stmt = _select_with_cursor_pagination(
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

        if page_size == 0:
            return RecordSet(records=records)
        else:
            if records:
                cursor = getattr(records[-1], sort_field)
            else:
                cursor = last_sort_value
            return RecordSet(
                records=records,
                pagination=CursorPagination(
                    cursor=str(cursor),
                    has_next=len(records) == page_size,
                ),
            )

    def _build_filter(self, filter: Operation | BooleanExpression) -> Column:
        if isinstance(filter, Operation):
            column: Column = getattr(self.__model_cls__, filter.field)

            if filter.operator == Operator.EQUALS:
                return column == filter.value
            elif filter.operator == Operator.NOT_EQUALS:
                return column != filter.value
            elif filter.operator == Operator.LESS_THAN:
                return column < filter.value
            elif filter.operator == Operator.GREATER_THAN:
                return column > filter.value
            elif filter.operator == Operator.LESS_THAN_OR_EQUAL:
                return column <= filter.value
            elif filter.operator == Operator.GREATER_THAN_OR_EQUAL:
                return column >= filter.value
            elif filter.operator == Operator.IN:
                return column.in_(filter.value)
            elif filter.operator == Operator.NOT_IN:
                return column.notin_(filter.value)
            elif filter.operator == Operator.CONTAINS:
                return column.contains(filter.value)
            elif filter.operator == Operator.STARTS_WITH:
                return column.startswith(filter.value)
            elif filter.operator == Operator.ENDS_WITH:
                return column.endswith(filter.value)
            elif filter.operator == Operator.NULL:
                return column.is_(None)
            elif filter.operator == Operator.NOT_NULL:
                return column.is_not(None)
            elif filter.operator == Operator.BETWEEN:
                return column.between(*filter.value)
            elif filter.operator == Operator.NOT_BETWEEN:
                return ~column.between(*filter.value)

        elif isinstance(filter, BooleanExpression):
            sub_filters = [self._build_filter(sub_filter) for sub_filter in filter.value]

            if filter.operator == BooleanOperator.OR:
                return or_(*sub_filters)
            elif filter.operator == BooleanOperator.AND:
                return and_(*sub_filters)

        raise ValueError(f"Unsupported filter type: {type(filter)}")

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


def _select_with_cursor_pagination(
    stmt: Select,
    sort_col: Column,
    unique_col: Column,
    ascending: bool = True,
    last_sort_value=None,
    last_unique_value=None,
    filter: BooleanExpression | Operation | None = None,
    page_size: int = 10,
):
    subquery = stmt.subquery()
    sort_order = asc if ascending else desc

    subquery_sort_col = subquery.c[sort_col.name]
    subquery_unique_col = subquery.c[unique_col.name]

    pagination_stmt = select(subquery).order_by(sort_order(subquery_sort_col), sort_order(subquery_unique_col))

    # apply filter if provided
    if filter is not None:
        # TODO: implement filter
        pass

    if last_sort_value is not None and last_unique_value is not None:
        condition = or_(
            (subquery_sort_col > last_sort_value if ascending else subquery_sort_col < last_sort_value),
            and_(
                subquery_sort_col == last_sort_value,
                (subquery_unique_col > last_unique_value if ascending else subquery_unique_col < last_unique_value),
            ),
        )
        pagination_stmt = pagination_stmt.where(condition)

    return pagination_stmt.limit(page_size)


__all__ = [
    "NotFoundError",
    "BaseRepository",
]
