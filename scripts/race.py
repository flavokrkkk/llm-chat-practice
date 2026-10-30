import asyncio

import httpx

API_URL = "http://127.0.0.1:8080/api/v1"


USER_A_ID = "0001fdf8-b2c9-43a9-9c3a-8c5816ea127e"  # Отправитель
USER_B_ID = "00066c83-148e-4ef4-a182-09cabd187f8d"  # Получатель

CONCURRENT_REQUESTS = 50
TRANSFER_AMOUNT = 100.0


async def send_transfer(client: httpx.AsyncClient, index: int):
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
