from pydantic_settings import BaseSettings


class BaseService:
    def __init__(self, settings: BaseSettings | None = None) -> None:
        self.settings = settings


__all__ = [
    "BaseService",
]
