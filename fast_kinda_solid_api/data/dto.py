from datetime import datetime

from fast_kinda_solid_api.data.convertible import ConvertibleBaseModel


class BaseDTO(ConvertibleBaseModel):
    """
    Generic Data Transfer Object (DTO) base class intended to be subclassed for specific use cases.
    Subclasses typically do not need to implement the interface methods unless custom logic is required.
    """

    pass


class BaseRecordDTO(BaseDTO):
    """
    A base DTO for records that typically include identifiers and timestamps for creation, update, and deletion.
    """

    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class BaseUpdateDTO(BaseDTO):
    """
    A base DTO designed for handling updates, including the necessary identifier for the entity being updated.
    """

    id: str


__all__ = [
    "BaseDTO",
    "BaseRecordDTO",
    "BaseUpdateDTO",
]
