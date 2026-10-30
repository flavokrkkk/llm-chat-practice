import asyncio
import functools
import logging
import random
from typing import Awaitable, Callable

from sqlalchemy.exc import DBAPIError

from app.infrastructure.errors.error_handlers import is_transient

logger = logging.getLogger(__name__)


def retry_on_transient_db_error[**P, R](
    max_attempts: int = 5, delay: float = 0.05, backoff_factor: float = 2.0
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Декоратор повторов для временных ошибок БД (сериализация, дедлоки).

    Транзакции, прерванные ошибкой, автоматически откатываются на уровне
    asyncpg, поэтому повтор операция безопасен: повторяем её с экспоненциальной
    задержкой и джиттером.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, max_attempts):
                try:
                    return await func(*args, **kwargs)
                except DBAPIError as exc:
                    if not is_transient(exc):
                        raise
                    if attempt >= max_attempts:
                        logger.error(
                            "Transient DB error not resolved after %s attempts: %s",
                            max_attempts,
                            args,
                        )
                        raise

                    sleep_time = delay * (
                        backoff_factor ** (attempt - 1)
                    ) + random.uniform(0, delay)
                    logger.warning(
                        "Transient DB error on attempt %s/%s, retrying in %.2fs",
                        attempt,
                        max_attempts,
                        sleep_time,
                    )
                    await asyncio.sleep(sleep_time)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
