from tests.fixtures.models import TestBase


def test_to_dict_unset_fields():
    """
    Ensure that from_dict method correctly handles unset fields.
    """
    model = TestBase.from_dict({"not_nullable_no_default": "1"})
    model.nullable_with_default_none_set = "2"

    model_dict = model.to_dict(exclude_unset=True)
    assert model_dict["not_nullable_no_default"] == "1"
    assert model_dict["nullable_with_default_none_set"] == "2"
    assert "nullable_with_default" not in model_dict
    assert "nullable_with_default_none" not in model_dict
