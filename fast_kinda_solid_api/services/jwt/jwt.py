import uuid
from datetime import UTC, datetime, timedelta
from typing import List

import jwt
from pydantic_settings import BaseSettings

from fast_kinda_solid_api.services.jwt.jwk import JWKValidationService
from fast_kinda_solid_api.services.jwt.schemas import JWT


class TokenServiceSettings(BaseSettings):
    secret_name: str
    algorithm: str = "HS256"
    access_token_expiry_minutes: int = 10
    id_token_expiry_minutes: int = 10
    issuer: str
    access_token_audience: str
    id_token_audience: str


class JWTService:
    """
    A service for creating and decoding JWTs for authentication and authorization.
    """

    def __init__(self, settings: TokenServiceSettings, secret_key: str, jwk_validation_service: JWKValidationService):
        """
        Initialize the JWT service.

        Args:
            settings (TokenServiceSettings): The settings for the JWT service.
            secret_key (str): The secret key to use for encoding and decoding JWTs.
            jwk_validation_service (JWKValidationService): The service to use for validating JWKs.
        """
        self.settings = settings
        self.secret_key = secret_key
        self.jwk_validation_service = jwk_validation_service

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

        token = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.settings.algorithm)

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
        """
        await self.jwk_validation_service.validate_id_token(
            token, self.settings.id_token_audience, self.settings.issuer
        )

        decoded = jwt.decode(token, self.secret_key, algorithms=[self.settings.algorithm])
        return JWT(**decoded)
