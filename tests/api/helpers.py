import httpx

from app.utils.cookie import REFRESH_TOKEN_COOKIE_KEY


async def login(client, user: dict) -> dict:
    """Логинит пользователя, возвращает заголовки с access-токеном."""
    r = await client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def login_response(client, user: dict) -> httpx.Response:
    r = await client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert r.status_code == 200, r.text
    return r


async def create_chat(client, headers: dict, title: str = "Test chat") -> str:
    r = await client.post("/chats", json={"title": title}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def refresh(client, token: str) -> httpx.Response:
    """Отправляет refresh именно с этим токеном."""
    client.cookies.clear()
    return await client.post(
        "/auth/refresh", headers={"Cookie": f"{REFRESH_TOKEN_COOKIE_KEY}={token}"}
    )


async def logout(client, token: str) -> httpx.Response:
    client.cookies.clear()
    return await client.post(
        "/auth/logout", headers={"Cookie": f"{REFRESH_TOKEN_COOKIE_KEY}={token}"}
    )
