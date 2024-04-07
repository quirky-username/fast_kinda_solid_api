import pytest

from fast_kinda_solid_api.services.aws.secrets_manager import (
    AWSSecretsManagerService,
    AWSSettings,
)
from fast_kinda_solid_api.services.base.secrets import SecretNotFoundError

settings = AWSSettings(
    REGION="us-east-1",
    ACCESS_KEY_ID="fake_access_key",
    SECRET_ACCESS_KEY="fake_secret_key",
    ENDPOINT_URL="http://localhost:4566",
)


@pytest.mark.asyncio
async def test_set_and_get_secret_success():
    secret_name = "test_secret"
    secret_value = "test_value"

    async with AWSSecretsManagerService(settings=settings) as service:
        await service.set_secret(secret_name, secret_value)
        fetched_secret = await service.get_secret(secret_name)

    assert fetched_secret == secret_value


@pytest.mark.asyncio
async def test_get_secret_not_found():
    secret_name = "non_existent_secret"

    async with AWSSecretsManagerService(settings=settings) as service:
        with pytest.raises(SecretNotFoundError):
            await service.get_secret(secret_name)
