import asyncio
from uuid import uuid4

import httpx

API_URL = "http://127.0.0.1:8080/api/v1"


TRANSFER_AMOUNT = "20.00"

user_a = {
    "id": "6e26174a-f72e-4611-9c55-bd16ec7f5764",
    "email": "egor@example.com",
    "password": "03432003",
}
user_b = {
    "id": "45b55363-91f1-4430-bde2-0f94e94226ee",
    "email": "mago@example.com",
    "password": "12345678",
}


async def login(client: httpx.AsyncClient, login_payload: dict[str, str]):

    payload = {"email": login_payload["email"], "password": login_payload["password"]}
    try:
        response = await client.post(
            f"{API_URL}/auth/login",
            json=payload,
        )
        return {"id": login_payload["id"], **response.json()}
    except Exception as e:
        return 500, str(e)


async def send_transfer(client: httpx.AsyncClient, token: str, to_user_id: str):
    payload = {
        "to_user_id": to_user_id,
        "amount": TRANSFER_AMOUNT,
    }
    try:
        response = await client.post(
            f"{API_URL}/transfers",
            json=payload,
            headers={
                "Idempotency-Key": f"abc-{str(uuid4())}",
                "Authorization": f"Bearer {token}",
            },
        )
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)


async def main():
    async with httpx.AsyncClient(trust_env=False, follow_redirects=True) as client:
        token_a, token_b = await asyncio.gather(
            *[login(client, user_a), login(client, user_b)]
        )

        if not isinstance(token_a, tuple) and not isinstance(token_b, tuple):
            tasks = [
                send_transfer(client, token_a["access_token"], to_user_id=user_b["id"])
                for _ in range(10)
            ] + [
                send_transfer(client, token_b["access_token"], to_user_id=user_a["id"])
                for _ in range(10)
            ]
            res = await asyncio.gather(*tasks)

            for x in res:
                print("Результат", x)


if __name__ == "__main__":
    asyncio.run(main())
