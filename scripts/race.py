import asyncio
from uuid import uuid4

import httpx

API_URL = "http://127.0.0.1:8080/api/v1"


USER_A_ID = "000d0dd1-5f44-4016-bee1-9af76d1ddb9b"  # Отправитель
USER_B_ID = "00106854-30ae-4ab0-bf44-6f5802b541ed"  # Получатель

CONCURRENT_REQUESTS = 50
TRANSFER_AMOUNT = "20.00"


async def send_transfer(client: httpx.AsyncClient, index: int):
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


async def main():

    print(f"Запускаем {CONCURRENT_REQUESTS} параллельных переводов...")

    limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
    async with httpx.AsyncClient(
        limits=limits, timeout=30.0, trust_env=False, follow_redirects=True
    ) as client:
        tasks = [send_transfer(client, i) for i in range(CONCURRENT_REQUESTS)]

        results = await asyncio.gather(*tasks)

        for status, text in results[:3]:
            print(f"Status: {status}, Response: {text}")

    success_count = sum(1 for status, _ in results if status == 200)
    failed_count = sum(1 for status, _ in results if status != 200)

    print("\n--- РЕЗУЛЬТАТЫ ГОНКИ ---")
    print(f"Успешных переводов: {success_count} (ожидалось максимум 10!)")
    print(f"Отклоненных переводов: {failed_count}")


if __name__ == "__main__":
    asyncio.run(main())
