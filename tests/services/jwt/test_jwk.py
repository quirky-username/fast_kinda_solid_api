import base64
import os
from datetime import datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from fast_kinda_solid_api.components.tokens.jwk import (
    ExpiredTokenError,
    JWKServiceSettings,
    JWKValidationService,
    TokenValidationError,
)


@pytest.fixture
def rsa_key():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return key


@pytest.fixture
def ec_key():
    key = ec.generate_private_key(ec.SECP256R1())
    return key


@pytest.fixture
def oct_key():
    return os.urandom(32)


@pytest.fixture
def okp_key():
    return ed25519.Ed25519PrivateKey.generate()


@pytest.fixture
def jwks_uri():
    return "https://example.com/.well-known/jwks.json"


@pytest.fixture
def jwks_service(jwks_uri):
    settings = JWKServiceSettings(jwks_uris={"example": jwks_uri}, refresh_interval=timedelta(hours=1))
    return JWKValidationService(settings)


def base64url_encode(data):
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def generate_jwk(key, kid, kty):
    if kty == "RSA":
        public_key = key.public_key()
        public_numbers = public_key.public_numbers()
        return {
            "kty": kty,
            "kid": kid,
            "use": "sig",
            "alg": "RS256",
            "n": base64url_encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, byteorder="big")),
            "e": base64url_encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, byteorder="big")),
        }
    elif kty == "EC":
        public_key = key.public_key()
        public_numbers = public_key.public_numbers()
        return {
            "kty": kty,
            "kid": kid,
            "use": "sig",
            "alg": "ES256",
            "crv": "P-256",
            "x": base64url_encode(public_numbers.x.to_bytes((public_numbers.x.bit_length() + 7) // 8, byteorder="big")),
            "y": base64url_encode(public_numbers.y.to_bytes((public_numbers.y.bit_length() + 7) // 8, byteorder="big")),
        }
    elif kty == "oct":
        return {"kty": kty, "kid": kid, "use": "sig", "alg": "HS256", "k": base64url_encode(key)}
    elif kty == "OKP":
        public_key = key.public_key()
        public_bytes = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)
        return {
            "kty": kty,
            "kid": kid,
            "use": "sig",
            "alg": "EdDSA",
            "crv": "Ed25519",
            "x": base64url_encode(public_bytes),
        }
    else:
        raise ValueError("Unsupported key type")


def create_token(key, kid, kty, client_id, issuer, exp=None):
    headers = {
        "kid": kid,
        "alg": "RS256" if kty == "RSA" else "ES256" if kty == "EC" else "HS256" if kty == "oct" else "EdDSA",
    }
    payload = {"sub": "1234567890", "name": "John Doe", "admin": True, "iss": issuer, "aud": client_id}
    if exp:
        payload["exp"] = exp
    if kty == "oct":
        return jwt.encode(payload, key, algorithm=headers["alg"], headers=headers)
    return jwt.encode(payload, key, algorithm=headers["alg"], headers=headers)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key_fixture, kid, kty, alg",
    [
        ("rsa_key", "rsa-key-1", "RSA", "RS256"),
        ("ec_key", "ec-key-1", "EC", "ES256"),
        ("oct_key", "oct-key-1", "oct", "HS256"),
        ("okp_key", "okp-key-1", "OKP", "EdDSA"),
    ],
)
async def test_validate_id_token(key_fixture, kid, kty, alg, request, jwks_service, jwks_uri, httpx_mock):
    key = request.getfixturevalue(key_fixture)
    client_id = "client_id"
    issuer = "example"
    token = create_token(key, kid, kty, client_id, issuer)

    jwk = generate_jwk(key, kid, kty)
    httpx_mock.add_response(url=jwks_uri, json={"keys": [jwk]})

    decoded_token = await jwks_service.validate_id_token(token, client_id, issuer)

    assert decoded_token["sub"] == "1234567890"


@pytest.mark.asyncio
async def test_validate_expired_token(rsa_key, jwks_service, jwks_uri, httpx_mock):
    kid = "rsa-key-1"
    kty = "RSA"
    client_id = "client_id"
    issuer = "example"
    exp = datetime.utcnow() - timedelta(seconds=1)
    token = create_token(rsa_key, kid, kty, client_id, issuer, exp=exp)

    jwk = generate_jwk(rsa_key, kid, kty)
    httpx_mock.add_response(url=jwks_uri, json={"keys": [jwk]})

    with pytest.raises(ExpiredTokenError):
        await jwks_service.validate_id_token(token, client_id, issuer)


@pytest.mark.asyncio
async def test_validate_invalid_signature(rsa_key, jwks_service, jwks_uri, httpx_mock):
    kid = "rsa-key-1"
    kty = "RSA"
    client_id = "client_id"
    issuer = "example"
    token = create_token(rsa_key, kid, kty, client_id, issuer)

    # Tamper with the signature by modifying the payload
    token_parts = token.split(".")
    tampered_payload = base64.urlsafe_b64encode(b'{"sub":"tampered"}').decode("utf-8").rstrip("=")
    tampered_token = f"{token_parts[0]}.{tampered_payload}.{token_parts[2]}"

    jwk = generate_jwk(rsa_key, kid, kty)
    httpx_mock.add_response(url=jwks_uri, json={"keys": [jwk]})

    with pytest.raises(TokenValidationError):
        await jwks_service.validate_id_token(tampered_token, client_id, issuer)
