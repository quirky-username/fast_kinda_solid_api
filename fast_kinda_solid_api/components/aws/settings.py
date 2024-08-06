from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWS_")

    ACCESS_KEY_ID: str | None = None
    SECRET_ACCESS_KEY: str | None = None
    REGION: str | None = None
    SESSION_TOKEN: str | None = None
    ENDPOINT_URL: str | None = None
    PROFILE_NAME: str | None = None


__all__ = [
    "AWSSettings",
]
