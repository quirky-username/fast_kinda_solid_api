import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import List

import jwt
from pydantic import Field
from pydantic_settings import BaseSettings

from fast_kinda_solid_api.components.tokens.jwk import JWKValidationService
from fast_kinda_solid_api.components.tokens.schemas import JWT
from fast_kinda_solid_api.core.layers.service import BaseService


class EncryptionAlgorithm(StrEnum):
    """
    Enumeration of supported encryption algorithms.
    """

    RS256 = "RS256"
    ES256 = "ES256"
    HS256 = "HS256"
    EdDSA = "EdDSA"


class JWTServiceSettings(BaseSettings):
    """
    Settings for the JWT service to use for creating and decoding tokens.
    """

    secret_name: str = Field(..., description="The name of the secret to use for encoding and decoding JWTs.")
    algorithm: EncryptionAlgorithm = Field(
        EncryptionAlgorithm.HS256,
        description="The algorithm to use for encoding and decoding JWTs.",
    )
    access_token_expiry_minutes: int = Field(10, description="The number of minutes until the access token expires.")
    id_token_expiry_minutes: int = Field(10, description="The number of minutes until the ID token expires.")
    issuer: str = Field(..., description="The issuer to use for the JWTs. This should be the API URL.")
    access_token_audience: str = Field(..., description="The audience for access tokens. This should be the API URL.")
    id_token_audience: str = Field(..., description="The audience for ID tokens. This should be the client ID.")


class JWTService(BaseService):
    """
    A service for creating and decoding JWTs for authentication and authorization.
    """

    settings: JWTServiceSettings

    def __init__(self, settings: JWTServiceSettings, secret_key: str, jwk_validation_service: JWKValidationService):
        """
        Initialize the JWT service.

        Args:
            settings (TokenServiceSettings): The settings to use for the service.
            secret_key (str): The secret key to use for encoding and decoding JWTs.
            jwk_validation_service (JWKValidationService): The service to use for validating JWKs.
        """
        super().__init__(settings)
        self._secret_key = secret_key
        self._jwk_validation_service = jwk_validation_service

    def _create_token(self, user_id: str, audience: str, expiry_minutes: int, **additional_claims) -> str:
        now = datetime.now(UTC)
        expiration = now + timedelta(minutes=expiry_minutes)
        payload = JWT(
            iss=self.settings.issuer,
            sub=user_id,
            aud=audience,
            exp=expiration,
            nbf=now,
            iat=now,
            jti=str(uuid.uuid4()),
            **additional_claims,
        )

        token = jwt.encode(payload.model_dump(), self._secret_key, algorithm=self.settings.algorithm)

        return token

    def create_access_token(self, user_id: str, scopes: List[str]) -> str:
        """
        Create an access token for a user with the given scopes.

        Args:
            user_id (str): The user ID for the token.
            scopes (List[str]): The scopes for the token.

        Returns:
            str: The generated access token.
        """
        additional_claims = {"scope": scopes}
        return self._create_token(
            user_id,
            self.settings.access_token_audience,
            self.settings.access_token_expiry_minutes,
            **additional_claims,
        )

    def create_id_token(self, user_id: str, user_info: dict) -> str:
        """
        Create an ID token for a user with the given user info.

        Args:
            user_id (str): The user ID for the token.
            user_info (dict): The user info to include in the token.

        Returns:
            str: The generated ID token.
        """
        return self._create_token(
            user_id,
            self.settings.id_token_audience,
            self.settings.id_token_expiry_minutes,
            **user_info,
        )

    async def decode_token(self, token: str) -> JWT:
        """
        Decode a token and return the payload.

        Args:
            token (str): The token to decode.

        Returns:
            JWT: The decoded token.

        Raises:
            ExpiredTokenError: If the token has expired.
            TokenValidationError: If the token is invalid
        """
        await self._jwk_validation_service.validate_id_token(
            token, self.settings.id_token_audience, self.settings.issuer
        )

        decoded = jwt.decode(
            token,
            self._secret_key,
            algorithms=[self.settings.algorithm],
            audience=self.settings.id_token_audience,
            issuer=self.settings.issuer,
        )

        return JWT(**decoded)


__all__ = [
    "JWTService",
    "JWTServiceSettings",
    "EncryptionAlgorithm",
]
