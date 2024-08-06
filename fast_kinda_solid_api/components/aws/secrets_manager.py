import aioboto3
import structlog

from fast_kinda_solid_api.components.base.secrets import (
    BaseSecretManagerService,
    SecretNotFoundError,
)

from .settings import AWSSettings

logger = structlog.getLogger(__name__)


class AWSSecretsManagerService(BaseSecretManagerService):
    """
    Service to interact with the AWS Secrets Manager.
    """

    settings: AWSSettings

    def __init__(self, settings: AWSSettings) -> None:
        """
        Initialize the service with the settings.

        Args:
            settings (AWSSettings): The settings to use.
        """
        super().__init__(settings)
        self.session = aioboto3.Session(
            region_name=settings.REGION,
            aws_access_key_id=settings.ACCESS_KEY_ID,
            aws_secret_access_key=settings.SECRET_ACCESS_KEY,
            profile_name=settings.PROFILE_NAME,
        )

    async def __aenter__(self):
        """
        Create the client when entering the context manager.

        Returns:
            AWSSecretsManagerService: The service instance.
        """
        self.client_builder = self.session.client(
            "secretsmanager",
            endpoint_url=self.settings.ENDPOINT_URL,
        )
        self.client = await self.client_builder.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Close the client when exiting the context manager.
        """
        await self.client_builder.__aexit__(exc_type, exc_value, traceback)

    async def get_secret(self, secret_name: str) -> str:
        """
        Get a secret from the AWS Secrets Manager.

        Args:
            secret_name (str): The name of the secret to get.

        Returns:
            str: The value of the secret.

        Raises:
            SecretNotFoundError: If the secret does not exist.
        """
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
        """
        Set a secret in the AWS Secrets Manager.

        Args:
            secret_name (str): The name of the secret to set.
            secret_value (str): The value of the secret to set.
        """
        try:
            logger.debug(f"Setting secret: {secret_name}")
            await self.client.create_secret(Name=secret_name, SecretString=secret_value)
        except Exception as e:
            resource_exists = hasattr(e, "response") and e.response["Error"]["Code"] == "ResourceExistsException"

            # if the resource does not exist and it failed to create it, raise the exception
            if not resource_exists:
                logger.error(f"Error setting secret {secret_name}: {e}")
                raise

        logger.debug(f"Setting secret: {secret_name}")
        await self.client.put_secret_value(SecretId=secret_name, SecretString=secret_value)


__all__ = [
    "AWSSecretsManagerService",
    "AWSSettings",
]
