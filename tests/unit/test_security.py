import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import SecretStr

from app.core.security import JWTManager
from app.infrastructure.config.config import JWTConfig
from app.infrastructure.errors.auth_exceptions import InvalidTokenError

SECRET = "test-secret-" + "x" * 32
MISSING = object()


@pytest.fixture
def jwt_manager() -> JWTManager:
    return JWTManager(JWTConfig(secret=SecretStr(SECRET)))


def make_payload(**changes) -> dict:
    """Корректный payload; changes заменяют поля, MISSING — удаляет поле."""

    now = datetime.now(UTC)

    payload = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    for key, value in changes.items():
        if value is MISSING:
            payload.pop(key)
        else:
            payload[key] = value

    return payload


def test_valid_token_returns_user_id(jwt_manager):
    user_id = uuid.uuid4()

    token = jwt_manager.create_access_token(user_id)

    assert jwt_manager.verify_token(token) == user_id


def test_token_signed_with_other_secret_is_rejected(jwt_manager):
    other = JWTManager(JWTConfig(secret=SecretStr("other-secret-" + "y" * 32)))
    token = other.create_access_token(uuid.uuid4())

    with pytest.raises(InvalidTokenError):
        jwt_manager.verify_token(token)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(make_payload(sub=MISSING), id="no_sub"),
        pytest.param(make_payload(sub="avc"), id="sub_not_uuid"),
        pytest.param(
            make_payload(exp=datetime.now(UTC) - timedelta(minutes=15)),
            id="exp_in_the_past",
        ),
        pytest.param(
            make_payload(sub=123),
            id="sub_is_int",
        ),
        pytest.param(make_payload(exp=MISSING), id="no_exp"),
        pytest.param(make_payload(iat=MISSING), id="no_iat"),
    ],
)
def test_token_with_bad_payload_is_rejected(jwt_manager, payload):
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        jwt_manager.verify_token(token)


def test_token_with_alg_none_is_rejected(jwt_manager):
    token = jwt.encode(make_payload(), None, algorithm="none")

    with pytest.raises(InvalidTokenError):
        jwt_manager.verify_token(token)
