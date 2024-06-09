from pydantic import Field

from fast_kinda_solid_api.domain.dto import ConvertibleBaseModel


class BaseSchema(ConvertibleBaseModel):
    pass


class RecordRequest(BaseSchema):
    """
    A request model representing a database record. This can be used as a base class or standalone.

    Attributes:
        id (UUID4): The unique identifier of the database record.
    """

    id: str = Field(description="The unique identifier of the database record")


__all__ = [
    "BaseSchema",
    "RecordRequest",
]
