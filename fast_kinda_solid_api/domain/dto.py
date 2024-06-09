from abc import abstractmethod
from datetime import datetime
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ConfigDict

from fast_kinda_solid_api.observability.logs import logger

T = TypeVar("T", bound="Convertible")


class Convertible:
    """
    Abstract base class for converting between different object types.
    Provides a common interface to standardize object conversion methods across different classes.
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Converts the object to a dictionary representation, which can be used to serialize
        or pass data to other systems.

        Returns:
            dict[str, Any]: A dictionary representation of the object.
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], value: dict[str, Any]) -> T:
        """
        Creates an instance of the class from a dictionary, allowing easy deserialization.

        Args:
            value (dict[str, Any]): A dictionary containing the object's data.

        Returns:
            T: An instance of the class.
        """
        pass

    @classmethod
    def convert_from(cls: Type[T], source: "Convertible", **values) -> T:
        """
        Converts from one object type to another using the dictionary representation,
        with an option to override or extend the original properties via additional values.

        Args:
            source (Convertible): The source object to convert from.
            **values: Additional key-value pairs to update in the source object's dictionary.

        Returns:
            T: An instance of the class based on the source object's data and additional values.
        """
        value = source.to_dict()
        value.update(values)
        return cls.from_dict(value)

    def merge(self, source: "Convertible") -> "Convertible":
        """
        Merges the current object with another object, updating its properties.

        Args:
            source (Convertible): The source object to merge from.

        Returns:
            Convertible: A new object that is the result of merging the source into this object.
        """
        return source.convert_from(self, **source.to_dict())


class ConvertibleBaseModel(Convertible, BaseModel):
    """
    A base model that is immutable after creation and supports validation on assignment.
    This class is meant to be subclassed by DTOs that require immutability and validation.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        copy_on_model_validation="deep",
        extra="allow",
    )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BaseDTO":
        """
        Create a model instance based on a dictionary of attributes, filtering only relevant keys.

        Args:
            value (dict[str, Any]): A dictionary containing the attributes of the model.

        Returns:
            BaseDTO: A new instance of BaseDTO with attributes set according to the input dictionary.
        """
        missing_keys = []
        filtered_value = {}
        for key in value.keys():
            if key in cls.model_fields:
                filtered_value[key] = value[key]
            else:
                missing_keys.append(key)

        if missing_keys:
            logger.debug(f"{cls.__qualname__} does not have the following keys: {missing_keys}")

        return cls.model_validate(filtered_value)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the model to a dictionary using model's serialization mechanism.

        Returns:
            dict[str, Any]: The dictionary representation of the model.
        """
        return {key: value for key, value in self.model_dump().items() if key in self.model_fields_set}


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
    "ConvertibleBaseModel",
    "BaseRecordDTO",
    "BaseUpdateDTO",
]
