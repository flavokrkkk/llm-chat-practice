import asyncio
import functools
import asyncpg


def retry_on_serialization_error(max_retries: int = 5, delay: float = 0.05):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except asyncpg.SerializationError:
                    print(f"Поймали SerializationError, попытка {attempt + 1}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
