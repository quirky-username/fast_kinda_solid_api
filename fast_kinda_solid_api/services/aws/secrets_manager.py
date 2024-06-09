import boto3

from fast_kinda_solid_api.core.layers.service import BaseService

from .settings import AWSSettings


class AWSSecretsManagerService(BaseService):
    def __init__(self, settings: AWSSettings) -> None:
        super().__init__(settings=settings)
        self.client = boto3.client(
            "secretsmanager",
            region_name=settings.region_name,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def get_secret_value(self, secret_name: str) -> str:
        response = self.client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
