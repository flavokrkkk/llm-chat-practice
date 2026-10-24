import asyncio
import functools
import logging
import random

import asyncpg

logger = logging.getLogger(__name__)

TRANSIENT_DB_ERRORS = (asyncpg.SerializationError, asyncpg.DeadlockDetectedError)


def retry_on_transient_db_error(
    max_retries: int = 5, delay: float = 0.05, backoff_factor: float = 2.0
):
    """Декоратор повторов для временных ошибок БД (сериализация, дедлоки).

    Транзакции, прерванные ошибкой, автоматически откатываются на уровне
    asyncpg, поэтому повтор операция безопасен: повторяем её с экспоненциальной
    задержкой и джиттером.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except TRANSIENT_DB_ERRORS:
                    if attempt >= max_retries:
                        logger.error(
                            "Transient DB error not resolved after %s attempts: %s",
                            max_retries,
                            args,
                        )
                        raise

                    sleep_time = delay * (backoff_factor ** (attempt - 1)) + random.uniform(
                        0, delay
                    )
                    logger.warning(
                        "Transient DB error on attempt %s/%s, retrying in %.2fs",
                        attempt,
                        max_retries,
                        sleep_time,
                    )
                    await asyncio.sleep(sleep_time)

        return wrapper

    return decorator
