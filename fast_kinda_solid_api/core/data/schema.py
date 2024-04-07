from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Generic, TypeVar

from pydantic import UUID4, BaseModel, Field

from fast_kinda_solid_api.core.data.convertible import ConvertibleBaseModel

TData = TypeVar("TData", bound="BaseModel")
TStatus = TypeVar("TStatus", bound="StrEnum")
TErrorCode = TypeVar("TErrorCode", bound="IntEnum")


class SkipPagination(BaseModel):
    total_items: int = Field(description="The total number of items")
    num_pages: int = Field(description="The total number of pages")
    page: int = Field(description="The current page number")


class CursorPagination(BaseModel):
    cursor: str = Field(description="The cursor for the next page")
    has_next: bool = Field(description="Whether there are more pages")


TPagination = CursorPagination | SkipPagination | None


class Error(BaseModel, Generic[TErrorCode]):
    code: TErrorCode = Field(description="The error code")
    message: str = Field(description="The error message")
    debug: str | None = None


class ApiResponse(ConvertibleBaseModel, Generic[TStatus, TData]):
    status: TStatus = Field(description="The API status for the response")
    data: TData | list[TData] | None = Field(None, description="The data returned by the API operation (optional)")
    pagination: TPagination = Field(None, description="The pagination information (optional)")
    error: Error | None = Field(None, description="The error information (optional)")


class BaseRecordResponse(BaseModel):
    """
    A response model representing a database record. This can be used as a base class or standalone.

    Attributes:
        id (UUID4): The unique identifier of the database record.
        created_at (datetime): The timestamp of when the record was originally created.
        updated_at (datetime): The timestamp of when the record was last updated.
        deleted_at (Optional[datetime]): The timestamp of when the record was deleted (optional).
    """

    id: UUID4 = Field(description="The unique identifier of the database record")
    created_at: datetime = Field(description="The timestamp of when the record was originally created")
    updated_at: datetime = Field(description="The timestamp of when the record was last updated")
    deleted_at: datetime | None = Field(None, description="The timestamp of when the record was deleted (optional)")


__all__ = [
    "SkipPagination",
    "CursorPagination",
    "TPagination",
    "Error",
    "ApiResponse",
    "BaseRecordResponse",
]
