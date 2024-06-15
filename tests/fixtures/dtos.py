from typing import Optional

from fast_kinda_solid_api.data.dto import BaseDTO, BaseRecordDTO, BaseUpdateDTO


class KeysetPaginatableCreate(BaseDTO):
    name: str
    order: int


class KeysetPaginatableUpdate(BaseUpdateDTO):
    name: str
    order: int


class KeysetPaginatableRecord(BaseRecordDTO):
    name: str
    order: int


class TestBaseRecord(BaseDTO):
    not_nullable_no_default: str
    nullable_with_default_none_set: Optional[str]
    nullable_with_default: Optional[str]
    nullable_with_default_none: Optional[str]
