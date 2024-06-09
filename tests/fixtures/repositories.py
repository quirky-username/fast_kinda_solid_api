from fast_kinda_solid_api.domain.repositories import RepositoryMixin
from tests.fixtures.models import KeysetPaginatableObject
from tests.fixtures.schemas import (
    KeysetPaginatableCreate,
    KeysetPaginatableRecord,
    KeysetPaginatableUpdate,
)


class PaginationRepository(RepositoryMixin[KeysetPaginatableCreate, KeysetPaginatableUpdate, KeysetPaginatableRecord]):
    __model_cls__ = KeysetPaginatableObject
    __record_cls__ = KeysetPaginatableRecord
