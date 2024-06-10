from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import UUID4, BaseModel, Field

from fast_kinda_solid_api.domain.dto import BaseDTO
from fast_kinda_solid_api.domain.schemas import BaseSchema

TRecord = TypeVar("TRecord", bound=BaseDTO)
TData = TypeVar("TData", bound=BaseSchema)


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    PROCESSING = "processing"
    INPUT_ERROR = "input_error"
    TRANSIENT_ERROR = "transient_error"
    NOT_FOUND = "not_found"


class PublicErrorResponse(BaseModel):
    code: str
    message: str


class PrivateErrorResponse(BaseModel):
    code: str
    message: str
    stacktrace: str


class PaginationMeta(BaseModel):
    current_page: int
    total_pages: int
    per_page: int
    total_items: int


class MetaData(BaseModel):
    request_id: str
    request_time: datetime
    response_time: datetime
    last_db_time: datetime


class Response(BaseSchema, Generic[TData]):
    data: TData | None = None
    message: str | None = None
    status: str = ResponseStatus.SUCCESS
    pagination: PaginationMeta | None = None
    errors: list[PrivateErrorResponse | PublicErrorResponse] | None = None
    meta: MetaData | None = None


class BaseRecordResponse(BaseSchema):
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
