from unittest.mock import Mock

import jwt
import pytest

from fast_kinda_solid_api.components.tokens.jwk import JWKValidationService
from fast_kinda_solid_api.components.tokens.jwt import JWTService, JWTServiceSettings

# Sample settings for the TokenService
settings = JWTServiceSettings(
    secret_name="my_secret",
    algorithm="HS256",
    access_token_expiry_minutes=10,
    id_token_expiry_minutes=10,
    issuer="my_issuer",
    access_token_audience="https://api.myservice.com",
    id_token_audience="my_client_app",
)

# Sample secret key
secret_key = "my_secret_key"

# Mock JWKValidationService
jwk_validation_service = Mock(spec=JWKValidationService)


@pytest.fixture
def jwt_service():
    """
    Fixture to provide a JWTService instance.
    """
    return JWTService(settings, secret_key, jwk_validation_service)


def test_create_access_token(jwt_service: JWTService):
    """
    Test creating an access token.
    """
    user_id = "user123"
    scopes = ["read", "write"]

    token = jwt_service.create_access_token(user_id, scopes)
    decoded = jwt.decode(token, secret_key, algorithms=[settings.algorithm], audience=settings.access_token_audience)

    assert decoded["iss"] == settings.issuer
    assert decoded["sub"] == user_id
    assert decoded["aud"] == settings.access_token_audience
    assert decoded["scope"] == scopes
    assert "exp" in decoded
    assert "nbf" in decoded
    assert "iat" in decoded
    assert "jti" in decoded


def test_create_id_token(jwt_service: JWTService):
    """
    Test creating an ID token.
    """
    user_id = "user123"
    user_info = {"name": "John Doe", "email": "john.doe@example.com"}

    token = jwt_service.create_id_token(user_id, user_info)
    decoded = jwt.decode(token, secret_key, algorithms=[settings.algorithm], audience=settings.id_token_audience)

    assert decoded["iss"] == settings.issuer
    assert decoded["sub"] == user_id
    assert decoded["aud"] == settings.id_token_audience
    assert decoded["name"] == user_info["name"]
    assert decoded["email"] == user_info["email"]
    assert "exp" in decoded
    assert "nbf" in decoded
    assert "iat" in decoded
    assert "jti" in decoded


@pytest.mark.asyncio
async def test_decode_token(jwt_service: JWTService):
    """
    Test decoding a token.
    """
    user_id = "user123"
    user_info = {"name": "John Doe", "email": "john.doe@example.com"}

    token = jwt_service.create_id_token(user_id, user_info)
    jwk_validation_service.validate_id_token.return_value = True  # Mock validation

    decoded = await jwt_service.decode_token(token)

    assert decoded.iss == settings.issuer
    assert decoded.sub == user_id
    assert decoded.aud == settings.id_token_audience
    assert decoded.name == user_info["name"]
    assert decoded.email == user_info["email"]
    assert decoded.exp is not None
    assert decoded.nbf is not None
    assert decoded.iat is not None
    assert decoded.jti is not None
