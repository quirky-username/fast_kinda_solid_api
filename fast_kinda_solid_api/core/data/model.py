import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from structlog import get_logger

from .convertible import Convertible

logger = get_logger(__name__)


class DbModel(Convertible):
    __abstract__ = True

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    def to_dict(self, exclude_unset: bool = False) -> dict[str, Any]:
        """
        Converts the object to a dictionary representation,
        which can be used to serialize or pass data to other systems.

        Args:
            exclude_unset (bool): Whether to exclude unset values from the dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the object.
        """
        data = {column.name: getattr(self, column.name) for column in self.__table__.columns}  # type: ignore
        if exclude_unset:
            return {key: value for key, value in data.items() if getattr(self, key) is not None}
        return data

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DbModel":
        """
        Creates an instance of the class from a dictionary, allowing easy deserialization.

        Args:
            value (dict[str, Any]): A dictionary containing the object's data.

        Returns:
            BaseModel: An instance of the class.
        """
        missing_keys = []
        filtered_value = {}
        for key, value in value.items():
            if key in cls.__mapper__.columns.keys():  # type: ignore
                filtered_value[key] = value
            else:
                missing_keys.append(key)

        logger.debug(f"{cls.__qualname__} does not have the following keys: {missing_keys}")
        return cls(**filtered_value)


class DbRecord(DbModel):
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


__all__ = [
    "DbModel",
    "DbRecord",
]
