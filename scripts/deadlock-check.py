import asyncio

import httpx

API_URL = "http://127.0.0.1:8080/api/v1"


USER_A_ID = "0001fdf8-b2c9-43a9-9c3a-8c5816ea127e"  # Отправитель
USER_B_ID = "00066c83-148e-4ef4-a182-09cabd187f8d"  # Получатель

TRANSFER_AMOUNT = 100.0


async def send_transfer_a(client: httpx.AsyncClient):
    payload = {
        "from_user_id": USER_A_ID,
        "to_user_id": USER_B_ID,
        "amount": TRANSFER_AMOUNT,
    }
    try:
        response = await client.post(f"{API_URL}/transfers", json=payload)
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
        response = await client.post(f"{API_URL}/transfers", json=payload)
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)


async def main():
    async with httpx.AsyncClient(trust_env=False, follow_redirects=True) as client:
        task1 = send_transfer_a(client)
        task2 = send_transfer_b(client)

        await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main())
