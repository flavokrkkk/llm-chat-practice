import uuid

import httpx
import pytest

BASE_URL = "http://localhost:8080/api/v1"
PASSWORD = "Str0ng-password!"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        yield c


@pytest.fixture
def make_user(client):
    async def _make() -> dict:
        data = {
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password": PASSWORD,
            "full_name": "Test User",
        }
        r = await client.post("/auth/register", json=data)
        assert r.status_code == 201, r.text
        return {**data, "id": r.json()["id"]}

    return _make
