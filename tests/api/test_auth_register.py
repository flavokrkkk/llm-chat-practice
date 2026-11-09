import uuid

import pytest

pytestmark = pytest.mark.api


async def test_register_returns_user_without_password(client):
    data = {
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "password": "Str0ng-password!",
        "full_name": "Test User",
    }

    r = await client.post("/auth/register", json=data)

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == data["email"]
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_same_email_other_case_returns_409(client, make_user):
    user = await make_user()

    r = await client.post(
        "/auth/register",
        json={
            "email": user["email"].upper(),
            "password": user["password"],
            "full_name": user["full_name"],
        },
    )

    assert r.status_code == 409, r.text
    body = r.json()
    assert body["detail"]["code"] == "EMAIL_ALREADY_REGISTERED"
    assert body["detail"]["request_id"] == r.headers["x-request-id"]


@pytest.mark.parametrize(
    "email",
    [
        pytest.param("123212", id="digits_only"),
        pytest.param("user_2222", id="no_at_sign"),
        pytest.param("user@", id="no_domain"),
        pytest.param("", id="empty"),
    ],
)
async def test_register_with_invalid_email_returns_422(client, email):
    data = {
        "email": email,
        "password": "Str0ng-password!",
        "full_name": "Test User",
    }
    r = await client.post("/auth/register", json=data)

    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "VALIDATION_ERROR"
