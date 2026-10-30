import asyncio
import json

import httpx

CHAT_ID = "00001a2a-c1b4-4215-81aa-1721f81b5653"
API_URL = "http://127.0.0.1:8080/api/v1"
CONCURRENT_REQUESTS = 20
IDEMPOTENCY_KEY = "unique_key_test_12345"


async def send_create_message(client: httpx.AsyncClient, index: int):
    payload = {"role": "user", "content": "Привет, мир! Проверка идемпотентности."}
    headers = {"Idempotency-Key": IDEMPOTENCY_KEY}
    try:
        response = await client.post(
            f"{API_URL}/chats/{CHAT_ID}/messages", json=payload, headers=headers
        )
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)


async def main():
    print(
        f"🚀 Запускаем {CONCURRENT_REQUESTS} одновременных запросов с одинаковым ключом: {IDEMPOTENCY_KEY}..."
    )

    async with httpx.AsyncClient(
        trust_env=False, follow_redirects=True, timeout=30.0
    ) as client:
        tasks = [send_create_message(client, i) for i in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)

    # Анализируем ответы
    status_codes = [status for status, _ in results]
    success_responses = [text for status, text in results if status == 200]

    # Собираем ID сообщений из ответов сервера
    message_ids = set()
    for text in success_responses:
        try:
            data = json.loads(text)
            message_ids.add(data.get("id"))
        except Exception:
            pass

    print("\n--- РЕЗУЛЬТАТЫ ТЕСТА ИДЕМПОТЕНТНОСТИ ---")
    print(f"Всего запросов: {len(results)}")
    print(f"Успешных (200 OK): {status_codes.count(200)}")
    print(f"Ошибок: {len(results) - status_codes.count(200)}")
    print(f"Уникальных ID сообщений в ответах: {len(message_ids)}")
    print(f"ID созданного сообщения: {list(message_ids)}")

    if len(message_ids) == 1 and status_codes.count(200) == CONCURRENT_REQUESTS:
        print(
            "\nИТОГ: ИДЕМПОТЕНТНОСТЬ РАБОТАЕТ ИДЕАЛЬНО! Все клиенты получили одно и то же сообщение!"
        )
    else:
        print("\nИТОГ: ЧТО-ТО ПОШЛО НЕ ТАК (создались дубликаты или были ошибки).")
        for status, text in results[:3]:
            print(f"Пример ответа ({status}): {text}")


if __name__ == "__main__":
    asyncio.run(main())
