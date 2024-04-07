from abc import abstractmethod

from fast_kinda_solid_api.core.layers.service import BaseService


class SecretNotFoundError(Exception):
    def __init__(self, secret_name: str, *args: object) -> None:
        super().__init__(
            f"Secrets Manager can't find the specified secret: {secret_name}",
            *args,
        )
        self.secret_name = secret_name


class BaseSecretManagerService(BaseService):
    @abstractmethod
    async def get_secret(self, secret_name: str) -> str:
        pass

    @abstractmethod
    async def set_secret(self, secret_name: str, secret_value: str) -> None:
        pass
