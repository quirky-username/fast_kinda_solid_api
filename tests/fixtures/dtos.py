from typing import Optional

from fast_kinda_solid_api.core.data.convertible import ConvertibleBaseModel
from fast_kinda_solid_api.core.data.dto import BaseRecord, BaseRecordReference


class KeysetPaginatableCreate(ConvertibleBaseModel):
    name: str
    order: int


class KeysetPaginatableUpdate(BaseRecordReference):
    name: str
    order: int


class KeysetPaginatableRecord(BaseRecord):
    name: str
    order: int


class TestBaseRecord(ConvertibleBaseModel):
    not_nullable_no_default: str
    nullable_with_default_none_set: Optional[str]
    nullable_with_default: Optional[str]
    nullable_with_default_none: Optional[str]
