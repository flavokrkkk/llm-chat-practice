import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.errors.auth_exceptions import (
    AccountDisabledError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.infrastructure.errors.error_handlers import register_exception_handlers
from app.infrastructure.errors.exceptions import (
    InsufficientFundsError,
    NotFoundError,
    RateLimitExceededError,
)
from app.infrastructure.middleware.logging_middleware import RequestIdMiddleware


def build_app() -> FastAPI:
    """Тестовое приложение с той же обработкой ошибок, что в проде."""

    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)
    return app


def make_client(exc: Exception) -> TestClient:
    """Клиент к приложению с одним эндпоинтом, который бросает exc."""

    app = build_app()

    @app.get("/raise")
    async def _raise() -> None:
        raise exc

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def validation_client() -> TestClient:
    app = build_app()

    @app.get("/validation")
    async def validation(limit: int = 10) -> dict:
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("exc", "status", "code"),
    [
        pytest.param(NotFoundError("Chat not found"), 404, "NOT_FOUND", id="not_found"),
        pytest.param(
            RateLimitExceededError("Rate limit exceeded"),
            429,
            "RATE_LIMIT_EXCEEDED",
            id="rate_limit",
        ),
        pytest.param(RuntimeError("boom"), 500, "INTERNAL_ERROR", id="unhandled"),
        pytest.param(
            InsufficientFundsError("Insufficient funds"),
            400,
            "INSUFFICIENT_FUNDS",
            id="insufficient_funds",
        ),
        pytest.param(
            EmailAlreadyRegisteredError("This email is already taken"),
            409,
            "EMAIL_ALREADY_REGISTERED",
            id="email_taken",
        ),
        pytest.param(
            InvalidCredentialsError("Incorrect email or password"),
            401,
            "INVALID_CREDENTIALS",
            id="invalid_credentials",
        ),
        pytest.param(
            InvalidTokenError("Failed to verify credentials"),
            401,
            "INVALID_TOKEN",
            id="invalid_token",
        ),
        pytest.param(
            AccountDisabledError("Your account is blocked!"),
            403,
            "ACCOUNT_DISABLED",
            id="account_disabled",
        ),
    ],
)
def test_exception_maps_to_status_and_code(exc, status, code):
    response = make_client(exc).get("/raise")

    assert response.status_code == status, response.text
    body = response.json()
    assert body["detail"]["code"] == code
    assert body["detail"]["request_id"] == response.headers["x-request-id"]
    assert body["detail"]["details"] == []


def test_validation_error_returns_422_with_details(validation_client):
    response = validation_client.get("/validation", params={"limit": "not-a-number"})

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "VALIDATION_ERROR"
    assert body["detail"]["message"] == "Validation error"
    assert body["detail"]["request_id"] == response.headers["x-request-id"]
    assert isinstance(body["detail"]["details"], list)
    assert len(body["detail"]["details"]) > 0
