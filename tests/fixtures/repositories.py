from fast_kinda_solid_api.repositories import RepositoryMixin
from tests.fixtures.dtos import (
    KeysetPaginatableCreate,
    KeysetPaginatableRecord,
    KeysetPaginatableUpdate,
)
from tests.fixtures.models import KeysetPaginatableObject


class PaginationRepository(RepositoryMixin[KeysetPaginatableCreate, KeysetPaginatableUpdate, KeysetPaginatableRecord]):
    __model_cls__ = KeysetPaginatableObject
    __record_cls__ = KeysetPaginatableRecord
