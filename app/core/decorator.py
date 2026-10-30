import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable

from sqlalchemy.exc import DBAPIError

from app.infrastructure.database.errors import get_sqlstate, is_transient

logger = logging.getLogger(__name__)


def retry_on_transient_db_error[**P, R](
    max_attempts: int = 5, delay: float = 0.05, backoff_factor: float = 2.0
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Повторяет вызов при временных ошибках БД (40001, 40P01) с экспоненциальной
    задержкой и джиттером.

    Декорируемая функция должна целиком содержать транзакцию
    (`async with session.begin()`): после ошибки транзакция откатывается,
    и повтор начинает новую. Если вызвать функцию внутри уже открытой
    транзакции, повтор пойдёт в прерванной транзакции и упадёт с
    `current transaction is aborted`.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, max_attempts):
                try:
                    return await func(*args, **kwargs)
                except DBAPIError as exc:
                    if not is_transient(exc):
                        raise

                    sleep_time = delay * (
                        backoff_factor ** (attempt - 1)
                    ) + random.uniform(0, delay)
                    logger.warning(
                        "Transient DB error in %s (sqlstate=%s), attempt %s/%s, retrying in %.2fs",
                        func.__qualname__,
                        get_sqlstate(exc),
                        attempt,
                        max_attempts,
                        sleep_time,
                    )
                    await asyncio.sleep(sleep_time)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
