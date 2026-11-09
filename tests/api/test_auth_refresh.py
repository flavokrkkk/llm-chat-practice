import pytest

from app.utils.cookie import REFRESH_TOKEN_COOKIE_KEY
from tests.api.helpers import login_response, logout, refresh

pytestmark = pytest.mark.api


def assert_invalid_token(r) -> None:
    assert r.status_code == 401, r.text
    assert r.json()["detail"]["code"] == "INVALID_TOKEN"


async def test_refresh_rotates_token(client, make_user):
    user = await make_user()
    old_token = (await login_response(client, user)).cookies[REFRESH_TOKEN_COOKIE_KEY]

    r = await refresh(client, old_token)

    assert r.status_code == 200, r.text
    assert "access_token" in r.json()
    assert r.cookies[REFRESH_TOKEN_COOKIE_KEY] != old_token


async def test_reused_refresh_token_revokes_whole_family(client, make_user):
    user = await make_user()
    old_token = (await login_response(client, user)).cookies[REFRESH_TOKEN_COOKIE_KEY]
    rotated = await refresh(client, old_token)
    assert rotated.status_code == 200, rotated.text
    new_token = rotated.cookies[REFRESH_TOKEN_COOKIE_KEY]

    reuse_response = await refresh(client, old_token)
    new_token_response = await refresh(client, new_token)

    assert_invalid_token(reuse_response)
    assert_invalid_token(new_token_response)


async def test_refresh_after_logout_returns_401(client, make_user):
    user = await make_user()
    token = (await login_response(client, user)).cookies[REFRESH_TOKEN_COOKIE_KEY]
    logout_response = await logout(client, token)
    assert logout_response.is_success, logout_response.text

    r = await refresh(client, token)

    assert_invalid_token(r)


async def test_refresh_without_cookie_returns_401(client):
    r = await client.post("/auth/refresh")

    assert r.status_code == 401, r.text


async def test_refresh_with_garbage_token_returns_401(client):
    r = await refresh(client, "garbage-token")

    assert_invalid_token(r)
