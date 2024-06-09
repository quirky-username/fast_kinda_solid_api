from abc import abstractmethod
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ConfigDict
from structlog import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound="Convertible")


class Convertible:
    """
    Abstract base class for converting between different object types.
    Provides a common interface to standardize object conversion methods across different classes.
    """

    @abstractmethod
    def to_dict(
        self,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
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
    def convert_from(
        cls: Type[T],
        source: "Convertible",
        exclude_unset: bool = False,
        **values,
    ) -> T:
        """
        Converts from one object type to another using the dictionary representation,
        with an option to override or extend the original properties via additional values.

        Args:
            source (Convertible): The source object to convert from.
            **values: Additional key-value pairs to update in the source object's dictionary.

        Returns:
            T: An instance of the class based on the source object's data and additional values.
        """
        value = source.to_dict(
            exclude_unset=exclude_unset,
        )
        value.update(values)
        result: T = cls.from_dict(value)
        return result

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
        frozen=False,
        validate_assignment=True,
        copy_on_model_validation="deep",
        extra="allow",
    )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ConvertibleBaseModel":
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
                if cls.model_fields[key].annotation == str:
                    filtered_value[key] = str(value[key])
                else:
                    filtered_value[key] = value[key]
            else:
                missing_keys.append(key)

        if missing_keys:
            logger.debug(f"{cls.__qualname__} does not have the following keys: {missing_keys}")

        return cls.model_validate(filtered_value)

    def to_dict(
        self,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        """
        Converts the object to a dictionary representation
        which can be used to serialize or pass data to other data models.
        """
        return self.model_dump(
            exclude_unset=exclude_unset,
        )


__all__ = [
    "Convertible",
    "ConvertibleBaseModel",
]
