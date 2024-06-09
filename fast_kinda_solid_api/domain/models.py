import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fast_kinda_solid_api.domain.dto import Convertible
from fast_kinda_solid_api.observability.logs import logger
from fast_kinda_solid_api.utils.time_and_date import serialize_datetime


class BaseTable(Convertible):
    __abstract__ = True

    class Config:
        json_encoders = {
            datetime: serialize_datetime,
        }

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def to_dict(self: DeclarativeBase) -> dict[str, Any]:
        return {
            field.name: _map_dto_value(field.type.python_type, getattr(self, field.name))
            for field in self.__mapper__.columns
        }

    @classmethod
    def from_dict(cls: DeclarativeBase, value: dict[str, Any]) -> "BaseTable":
        missing_keys = []
        filtered_value = {}
        for key, value in value.items():
            if key in cls.__mapper__.columns.keys():
                filtered_value[key] = value
            else:
                missing_keys.append(key)

        logger.debug(f"{cls.__qualname__} does not have the following keys: {missing_keys}")
        return cls(**filtered_value)


def _map_dto_value(value_type: type, value: Any):
    if value_type == str or issubclass(value_type, uuid.UUID):
        return str(value)

    return value


__all__ = [
    "BaseTable",
]
