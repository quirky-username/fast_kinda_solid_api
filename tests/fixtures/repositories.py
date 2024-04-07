from fast_kinda_solid_api.core.layers.repository import BaseRepository
from tests.fixtures.dtos import KeysetPaginatableRecord
from tests.fixtures.models import KeysetPaginatableObject


class PaginationRepository(BaseRepository[KeysetPaginatableRecord]):
    __model_cls__ = KeysetPaginatableObject
    __record_cls__ = KeysetPaginatableRecord
