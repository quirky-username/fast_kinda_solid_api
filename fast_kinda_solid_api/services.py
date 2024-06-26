from fast_kinda_solid_api.config import BaseServiceSettings


class BaseService:
    def __init__(self, settings: BaseServiceSettings | None = None) -> None:
        self.settings = settings


__all__ = [
    "BaseService",
]
