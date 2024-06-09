from fast_kinda_solid_api.domain.dto import BaseDTO, BaseRecordDTO, BaseUpdateDTO


class KeysetPaginatableCreate(BaseDTO):
    name: str
    order: int


class KeysetPaginatableUpdate(BaseUpdateDTO):
    name: str
    order: int


class KeysetPaginatableRecord(BaseRecordDTO):
    name: str
    order: int
