from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.errors.error_handlers import register_exception_handlers
from app.infrastructure.errors.exceptions import (
    InsufficientFundsError,
    NotFoundError,
    RateLimitExceededError,
)

app = FastAPI()


@app.get("/not-found")
async def not_found():
    raise NotFoundError("Chat not found")


@app.get("/insufficient-funds")
async def insufficient_funds():
    raise InsufficientFundsError("Недостаточно средств: 0 < 100")


@app.get("/rate-limited")
async def rate_limited():
    raise RateLimitExceededError("Rate limit exceeded")


@app.get("/boom")
async def boom():
    raise RuntimeError("boom")


@app.get("/validation")
async def validation(limit: int = 10):
    return {"ok": True}


register_exception_handlers(app)

client = TestClient(app, raise_server_exceptions=False)


def test_not_found_error_returns_consistent_body():
    response = client.get("/not-found")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["code"] == "NOT_FOUND"
    assert body["detail"]["message"] == "Chat not found"
    assert body["detail"]["details"] == []


def test_insufficient_funds_error_returns_400():
    response = client.get("/insufficient-funds")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INSUFFICIENT_FUNDS"
    assert response.json()["detail"]["message"] == "Недостаточно средств: 0 < 100"


def test_rate_limit_exceeded_returns_429():
    response = client.get("/rate-limited")

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_unhandled_exception_returns_500_internal_error():
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "INTERNAL_ERROR"
    assert response.json()["detail"]["message"] == "Internal server error"


def test_validation_error_returns_422_with_details():
    response = client.get("/validation", params={"limit": "not-a-number"})

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "VALIDATION_ERROR"
    assert body["detail"]["message"] == "Validation error"
    assert isinstance(body["detail"]["details"], list)
    assert len(body["detail"]["details"]) > 0
