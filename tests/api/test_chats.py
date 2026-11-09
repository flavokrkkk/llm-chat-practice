import pytest

from tests.api.helpers import create_chat, login

pytestmark = pytest.mark.api


async def test_foreign_chat_returns_404(client, make_user):
    owner = await make_user()
    stranger = await make_user()
    chat_id = await create_chat(client, await login(client, owner))

    r = await client.get(f"/chats/{chat_id}", headers=await login(client, stranger))

    assert r.status_code == 404, r.text


async def test_create_chat_returns_success(client, make_user):
    user = await make_user()

    r = await client.post(
        "/chats", json={"title": "Test chat"}, headers=await login(client, user)
    )

    assert r.status_code == 201, r.text
    body = r.json()
    assert "id" in body
    assert body["title"] == "Test chat"
    assert body["user_id"] == user["id"]


async def test_bad_token_chat_returns_401(client):
    r = await client.post(
        "/chats",
        json={"title": "Test chat"},
        headers={"Authorization": "Bearer bad-token"},
    )

    assert r.status_code == 401, r.text
    body = r.json()
    assert body["detail"]["code"] == "INVALID_TOKEN"


async def test_create_chat_without_token_returns_401(client):
    r = await client.post(
        "/chats",
        json={"title": "Test chat"},
    )

    assert r.status_code == 401, r.text
    body = r.json()
    assert body["detail"]["code"] == "UNAUTHORIZED"


async def test_create_chat_rejects_user_id_in_body(client, make_user):
    owner = await make_user()
    victim = await make_user()

    r = await client.post(
        "/chats",
        json={"title": "Test chat", "user_id": victim["id"]},
        headers=await login(client, owner),
    )

    assert r.status_code == 422, r.text
    details = r.json()["detail"]["details"]
    assert details[0]["loc"] == ["body", "user_id"]
