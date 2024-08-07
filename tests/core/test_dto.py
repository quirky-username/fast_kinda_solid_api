from datetime import datetime

import pytest
from pydantic import ValidationError

from fast_kinda_solid_api.core.data.convertible import ConvertibleBaseModel
from fast_kinda_solid_api.core.data.dto import BaseDTO, BaseRecord


# Fixtures
@pytest.fixture
def sample_record_dict():
    return {"id": "123", "created_at": datetime.now(), "updated_at": datetime.now(), "deleted_at": None}


@pytest.fixture
def sample_update_dict():
    return {"id": "update123"}


@pytest.fixture
def sample_nested_dict():
    return {
        "id": "nested123",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted_at": None,
        "nested": {"nested_id": "nested_id_456", "nested_value": "test"},
    }


def test_from_dict_method():
    """
    Ensure that from_dict method correctly sets attributes from a dictionary.
    """

    class TestDTO(BaseDTO):
        id: str
        created_at: datetime

    test_dict = {"id": "123", "created_at": datetime.now()}
    dto = TestDTO.from_dict(test_dict)
    assert dto.id == "123", "TestDTO should correctly set 'id'."
    assert dto.created_at == test_dict["created_at"], "TestDTO should correctly set 'created_at'."


def test_to_dict_unset_fields():
    """
    Ensure that from_dict method correctly handles unset fields.
    """

    class TestDTO(BaseDTO):
        not_nullable_no_default: str
        nullable_with_default_none_set: str | None = "-1"
        nullable_with_default: str | None = "3"
        nullable_with_default_none: str | None = None

    dto = TestDTO.from_dict({"not_nullable_no_default": "1"})
    dto.nullable_with_default_none_set = "2"
    dto_dict = dto.to_dict(exclude_unset=False)
    assert dto_dict["not_nullable_no_default"] == "1"
    assert dto_dict["nullable_with_default_none_set"] == "2"
    assert dto_dict["nullable_with_default"] == "3"
    assert dto_dict["nullable_with_default_none"] is None

    dto_dict = dto.to_dict(exclude_unset=True)
    assert dto_dict["not_nullable_no_default"] == "1"
    assert dto_dict["nullable_with_default_none_set"] == "2"
    assert "nullable_with_default" not in dto_dict
    assert "nullable_with_default_none" not in dto_dict


def test_convert_from_method():
    """
    Ensure that convert_from method correctly converts between DTO objects.
    """

    class SourceDTO(BaseDTO):
        id: str
        created_at: datetime
        extra: str

    class TargetDTO(BaseDTO):
        id: str
        created_at: datetime

    source = SourceDTO(id="1", created_at=datetime(2023, 1, 1), extra="extra")
    converted = TargetDTO.convert_from(source, id="2")
    assert converted.id == "2", "Converted DTO should have updated 'id'."
    assert converted.created_at == source.created_at, "Converted DTO should retain 'created_at' from source."


# Extended Tests for ConvertibleBaseModel with nested fields
def test_convertiblebasemodel_with_nested_fields(sample_nested_dict):
    """
    Ensure that ConvertibleBaseModel handles nested fields correctly.
    """

    class NestedModel(ConvertibleBaseModel):
        nested_id: str
        nested_value: str

    class TestModel(ConvertibleBaseModel):
        id: str
        created_at: datetime
        updated_at: datetime
        deleted_at: datetime | None
        nested: NestedModel

    test_dict = sample_nested_dict
    model = TestModel.from_dict(test_dict)
    assert model.id == "nested123", "TestModel should correctly set 'id'."
    assert model.nested.nested_id == "nested_id_456", "TestModel should correctly set nested 'nested_id'."
    assert model.nested.nested_value == "test", "TestModel should correctly set nested 'nested_value'."


def test_convertiblebasemodel_with_invalid_data():
    """
    Ensure that ConvertibleBaseModel raises validation errors for invalid data.
    """

    class TestModel(ConvertibleBaseModel):
        id: str
        created_at: datetime

    invalid_dict = {"id": "321", "created_at": "invalid_date"}
    with pytest.raises(ValidationError):
        TestModel.from_dict(invalid_dict)


def test_convertiblebasemodel_with_optional_fields():
    """
    Ensure that ConvertibleBaseModel handles optional fields correctly.
    """

    class TestModel(ConvertibleBaseModel):
        id: str
        created_at: datetime | None = None

    test_dict = {"id": "321"}
    model = TestModel.from_dict(test_dict)
    assert model.id == "321", "TestModel should correctly set 'id'."
    assert model.created_at is None, "TestModel should correctly handle missing 'created_at'."


# Extended Tests for BaseRecordDTO
def test_baserecorddto_with_missing_optional_fields(sample_record_dict):
    """
    Ensure that BaseRecordDTO handles missing optional fields correctly.
    """
    record_dict = sample_record_dict.copy()
    del record_dict["deleted_at"]
    record = BaseRecord.from_dict(record_dict)
    assert record.deleted_at is None, "BaseRecordDTO should handle missing optional 'deleted_at' field correctly."


def test_baserecorddto_with_invalid_data():
    """
    Ensure that BaseRecordDTO raises validation errors for invalid data.
    """
    invalid_dict = {"id": "123", "created_at": "invalid_date", "updated_at": datetime.now()}
    with pytest.raises(ValidationError):
        BaseRecord.from_dict(invalid_dict)


# Additional tests for merge and convert_from methods
def test_merge_method():
    """
    Ensure that merge method correctly merges two Convertible objects.
    """

    class TestModel(ConvertibleBaseModel):
        id: str
        created_at: datetime

    original = TestModel(id="1", created_at=datetime(2023, 1, 1))
    source = TestModel(id="2", created_at=datetime(2023, 1, 2))
    merged = original.merge(source)
    assert merged.id == "2", "Merged model should take 'id' from source."
    assert merged.created_at == datetime(2023, 1, 2), "Merged model should take 'created_at' from source."
