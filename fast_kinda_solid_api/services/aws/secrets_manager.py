import aioboto3
import boto3.exceptions
import structlog

from fast_kinda_solid_api.services.base.secrets import (
    BaseSecretManagerService,
    SecretNotFoundError,
)

from .settings import AWSSettings

logger = structlog.getLogger(__name__)


class AWSSecretsManagerService(BaseSecretManagerService):
    def __init__(self, settings: AWSSettings) -> None:
        super().__init__(settings=settings)
        self.settings = settings
        self.session = aioboto3.Session(
            region_name=settings.REGION,
            aws_access_key_id=settings.ACCESS_KEY_ID,
            aws_secret_access_key=settings.SECRET_ACCESS_KEY,
            profile_name=settings.PROFILE_NAME,
        )

    async def __aenter__(self):
        self.client_builder = self.session.client(
            "secretsmanager",
            endpoint_url=self.settings.ENDPOINT_URL,
        )
        self.client = await self.client_builder.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client_builder.__aexit__(exc_type, exc_value, traceback)

    async def get_secret(self, secret_name: str) -> str:
        try:
            logger.debug(f"Fetching secret: {secret_name}")
            response = await self.client.get_secret_value(SecretId=secret_name)
            return response["SecretString"]
        except Exception as e:
            if hasattr(e, "response") and e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(f"Secret {secret_name} not found")
                raise SecretNotFoundError(secret_name)
            raise e

    async def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            logger.debug(f"Setting secret: {secret_name}")
            await self.client._secret_value(SecretId=secret_name, SecretString=secret_value)
        except boto3.exceptions.Boto3Error as e:
            logger.error(f"Error setting secret {secret_name}: {e}")
            raise
