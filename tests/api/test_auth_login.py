import uuid

import pytest

pytestmark = pytest.mark.api


async def test_login_with_correct_password_returns_token(client, make_user):
    user = await make_user()

    r = await client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )

    assert r.status_code == 200, r.text
    assert "access_token" in r.json()


async def test_login_incorrect_password(client, make_user):
    user = await make_user()

    r = await client.post(
        "auth/login", json={"email": user["email"], "password": "incorrect_password"}
    )

    assert r.status_code == 401, r.text
    body = r.json()
    assert body["detail"]["code"] == "INVALID_CREDENTIALS"


async def test_login_unknown_email_and_wrong_password_look_the_same(client, make_user):
    user = await make_user()

    wrong_password = await client.post(
        "/auth/login", json={"email": user["email"], "password": "Wrong-password-1"}
    )
    unknown_email = await client.post(
        "/auth/login",
        json={
            "email": f"nobody-{uuid.uuid4().hex[:8]}@example.com",
            "password": "Wrong-password-1",
        },
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    a = wrong_password.json()["detail"]
    b = unknown_email.json()["detail"]
    assert a["code"] == b["code"] == "INVALID_CREDENTIALS"
    assert a["message"] == b["message"]
