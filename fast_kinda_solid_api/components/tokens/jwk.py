from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Literal

import httpx
import jwt
from fastapi import HTTPException
from jwt.algorithms import (
    Algorithm,
    ECAlgorithm,
    HMACAlgorithm,
    OKPAlgorithm,
    RSAAlgorithm,
)
from pydantic import Field
from pydantic_settings import BaseSettings

from fast_kinda_solid_api.core.layers.service import BaseService


class UnsupportedAlgorithmError(Exception):
    pass


class PublicKeyNotFoundError(Exception):
    pass


class ExpiredTokenError(Exception):
    pass


class TokenValidationError(Exception):
    pass


class JWKServiceSettings(BaseSettings):
    """
    Settings for the JWK service to use for fetching and validating JWKs.
    """

    jwks_uris: Dict[str, str] = Field(
        ...,
        description="The URIs of the JWKS endpoints for each issuer.",
    )
    refresh_interval: timedelta = Field(
        timedelta(hours=24),
        description="The interval at which to refresh the JWKS cache.",
    )


class JWKValidationService(BaseService):
    """
    A service for validating JWTs using JWKs.
    """

    settings: JWKServiceSettings

    def __init__(self, settings: JWKServiceSettings):
        """
        Initialize the JWK validation service.

        Args:
            settings (JWKServiceSettings): The settings to use for the service.
        """
        super().__init__(settings)
        self._jwks_cache: dict[str, dict[str, Any]] = {}
        self._last_refresh_time: dict[str, datetime] = {}

    async def _fetch_jwks(self, issuer: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.settings.jwks_uris[issuer])
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch JWKS")
            self._jwks_cache[issuer] = response.json()
            self._last_refresh_time[issuer] = datetime.now(UTC)

    def _should_refresh(self, issuer: str) -> bool:
        if issuer not in self._last_refresh_time:
            return True
        return datetime.now(UTC) - self._last_refresh_time[issuer] > self.settings.refresh_interval

    async def _get_public_key(self, kid: Literal["RSA", "EC", "oct", "OKP"], issuer: str) -> Algorithm:
        if self._should_refresh(issuer):
            await self._fetch_jwks(issuer)

        for key in self._jwks_cache[issuer]["keys"]:
            if key["kid"] == kid:
                if key["kty"] == "RSA":
                    return RSAAlgorithm.from_jwk(key)
                elif key["kty"] == "EC":
                    return ECAlgorithm.from_jwk(key)
                elif key["kty"] == "oct":
                    return HMACAlgorithm.from_jwk(key)
                elif key["kty"] == "OKP":
                    return OKPAlgorithm.from_jwk(key)
                else:
                    raise UnsupportedAlgorithmError()  # untested
        raise PublicKeyNotFoundError("Issuer responded with no matching public key")  # untested

    async def validate_id_token(self, id_token: str, client_id: str, issuer: str) -> Dict[str, Any]:
        """
        Validates a given ID token.

        Args:
            id_token (str): The ID token to validate.
            client_id (str): The client ID to validate against.
            issuer (str): The issuer to validate against.

        Returns:
            Dict[str, Any]: The decoded token if validation is successful.

        Raises:
            ExpiredTokenError: If the token has expired.
            TokenValidationError: If the token is invalid
        """
        unverified_header = jwt.get_unverified_header(id_token)
        public_key = await self._get_public_key(unverified_header["kid"], issuer)
        try:
            decoded_token = jwt.decode(
                id_token, public_key, audience=client_id, algorithms=[unverified_header["alg"]], issuer=issuer
            )
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError()
        except jwt.InvalidTokenError:
            raise TokenValidationError("Invalid ID token")
        return decoded_token
