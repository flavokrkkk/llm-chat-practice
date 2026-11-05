import asyncio
import time

import httpx

API_URL = "http://127.0.0.1:8080/api/v1"


user_a = {
    "email": "egor@example.com",
    "password": "03432003",
}


async def login(client: httpx.AsyncClient, login_payload: dict[str, str]):

    payload = {"email": login_payload["email"], "password": login_payload["password"]}
    try:
        response = await client.post(
            f"{API_URL}/auth/login",
            json=payload,
        )
        return response.json()
    except Exception as e:
        return 500, str(e)


async def health(client: httpx.AsyncClient):

    try:
        response = await client.get(
            f"{API_URL}/health",
        )
        return response.json()
    except Exception as e:
        return 500, str(e)


async def main():
    async with httpx.AsyncClient(trust_env=False, follow_redirects=True) as client:
        latencies: list[float] = []
        done = asyncio.Event()

        async def pinger(client):
            while not done.is_set():
                start = time.perf_counter()
                await health(client)
                latencies.append(time.perf_counter() - start)
                await asyncio.sleep(0.05)

        async def run_logins(client):
            await asyncio.gather(*[login(client, user_a) for _ in range(50)])
            done.set()

        await asyncio.gather(pinger(client), run_logins(client))


if __name__ == "main":
    asyncio.run(main())
