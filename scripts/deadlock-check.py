import asyncio
from uuid import uuid4

import httpx

API_URL = "http://127.0.0.1:8080/api/v1"


USER_A_ID = "000d0dd1-5f44-4016-bee1-9af76d1ddb9b"  # Отправитель
USER_B_ID = "00106854-30ae-4ab0-bf44-6f5802b541ed"  # Получатель

TRANSFER_AMOUNT = "20.00"


async def send_transfer_a(client: httpx.AsyncClient):
    payload = {
        "from_user_id": USER_A_ID,
        "to_user_id": USER_B_ID,
        "amount": TRANSFER_AMOUNT,
    }
    try:
        response = await client.post(
            f"{API_URL}/transfers",
            json=payload,
            headers={"Idempotency-Key": f"abc-{str(uuid4())}"},
        )
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)


async def send_transfer_b(client: httpx.AsyncClient):
    payload = {
        "from_user_id": USER_B_ID,
        "to_user_id": USER_A_ID,
        "amount": TRANSFER_AMOUNT,
    }
    try:
        response = await client.post(
            f"{API_URL}/transfers",
            json=payload,
            headers={"Idempotency-Key": f"abc-{str(uuid4())}"},
        )
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)


async def main():
    async with httpx.AsyncClient(trust_env=False, follow_redirects=True) as client:
        tasks = [send_transfer_a(client) for _ in range(10)] + [
            send_transfer_b(client) for _ in range(10)
        ]

        res = await asyncio.gather(*tasks)

        for x in res:
            print("Результат", x)


if __name__ == "__main__":
    asyncio.run(main())
