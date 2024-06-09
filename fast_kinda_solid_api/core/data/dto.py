from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar, Union

from pydantic import BaseModel, Field

from .convertible import ConvertibleBaseModel

TRecord = TypeVar("TRecord", bound="BaseRecord")


class BaseDTO(ConvertibleBaseModel):
    # TODO: for now this is overly general, but will be helpful for static analysis and type checking
    pass


class BaseRecord(BaseDTO):
    """
    A base DTO that represents a record in the database
    """

    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class BaseRecordReference(BaseDTO):
    """
    A base DTO that represents a reference to a record in the database
    """

    id: str


class SkipPagination(BaseModel):
    total_items: int
    num_pages: int
    page: int


class CursorPagination(BaseModel, Generic[TRecord]):
    cursor: str
    has_next: bool


class RecordSet(BaseModel, Generic[TRecord]):
    records: list[TRecord]
    pagination: CursorPagination | SkipPagination | None


class Operator(StrEnum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    LESS_THAN = "lt"
    GREATER_THAN = "gt"
    LESS_THAN_OR_EQUAL = "lte"
    GREATER_THAN_OR_EQUAL = "gte"
    IN = "in"
    NOT_IN = "nin"
    EVERY_ELEMENT_IN_ARRAY = "ina"
    NOT_EVERY_ELEMENT_IN_ARRAY = "nina"
    CONTAINS = "contains"
    NOT_CONTAINS = "ncontains"
    CONTAINS_CASE_SENSITIVE = "containss"
    NOT_CONTAINS_CASE_SENSITIVE = "ncontainss"
    BETWEEN = "between"
    NOT_BETWEEN = "nbetween"
    NULL = "null"
    NOT_NULL = "nnull"
    STARTS_WITH = "startswith"
    NOT_STARTS_WITH = "nstartswith"
    STARTS_WITH_CASE_SENSITIVE = "startswiths"
    NOT_STARTS_WITH_CASE_SENSITIVE = "nstartswiths"
    ENDS_WITH = "endswith"
    NOT_ENDS_WITH = "nendswith"
    ENDS_WITH_CASE_SENSITIVE = "endswiths"
    NOT_ENDS_WITH_CASE_SENSITIVE = "nendswiths"


class BooleanOperator(StrEnum):
    OR = "or"
    AND = "and"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class Operation(BaseModel):
    field: str = Field(..., description="The name of the field to filter on.")
    operator: Operator = Field(..., description="The operation to perform. Excludes logical operators 'or' and 'and'.")
    value: str | bool | float | int | datetime = Field(..., description="The value to filter by.")


class BooleanExpression(BaseModel):
    operator: BooleanOperator = Field(..., description="The logical operator to combine filters ('or' or 'and').")
    value: list[Union["Operation", "BooleanExpression"]] = Field(
        ..., description="An array of LogicalFilter or ConditionalFilter objects."
    )


class Sort(BaseModel):
    field: str = Field(..., description="The name of the field to sort by.")
    direction: SortDirection = Field(..., description="The direction to sort the field by.")


class Sorts(BaseModel):
    sorts: list[Sort] = Field(..., description="An array of Sort objects for applying multiple sorts simultaneously.")


# Adding recursion support for Pydantic models
Operation.model_rebuild()
BooleanExpression.model_rebuild()

__all__ = [
    "BaseDTO",
    "BaseRecord",
    "BaseRecordReference",
    "CursorPagination",
    "RecordSet",
    "SkipPagination",
]
