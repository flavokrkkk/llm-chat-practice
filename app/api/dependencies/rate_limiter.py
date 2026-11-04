import logging

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.schemas.auth import LoginRequest
from app.infrastructure.errors.exceptions import (
    RateLimitExceededError,
    ServiceUnavailableError,
)
from app.utils.enums import RateLimitScope

from .dependencies import CurrentUserDep, RedisDep

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(
        self,
        scope: RateLimitScope,
        limit: int = 10,
        window_seconds: int = 60,
        fail_open: bool = True,
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self.scope = scope
        self.fail_open = fail_open

    async def hit(self, redis: Redis, identity: str) -> None:
        key = f"rate_limit:{self.scope}:{identity}"

        try:
            async with redis.pipeline(transaction=True) as pipe:
                pipe.set(key, 0, ex=self.window, nx=True)
                pipe.incr(key)
                _, current = await pipe.execute()

        except RedisError:
            if self.fail_open:
                # Fail-open: при недоступности Redis не блокируем запросы,
                # чтобы не превратить сбой инфраструктуры в полный даун для клиентов.
                logger.warning(
                    "Rate limiter backend error, allow request. key=%s",
                    key,
                    exc_info=True,
                )
                return None

            logger.error(
                "Rate limiter backend error, allow request. key=%s",
                key,
                exc_info=True,
            )
            raise ServiceUnavailableError(
                "Concurrent update conflict, please retry the request"
            )

        if current > self.limit:
            raise RateLimitExceededError("Too Many Requests: Rate limit exceeded")


messages_limiter = RateLimiter(RateLimitScope.MESSAGES, limit=10, window_seconds=60)
login_limiter = RateLimiter(
    RateLimitScope.LOGIN, limit=5, window_seconds=300, fail_open=False
)


async def limit_messages(current_user: CurrentUserDep, redis: RedisDep) -> None:
    await messages_limiter.hit(redis, identity=str(current_user.id))


async def limit_login(request: Request, payload: LoginRequest, redis: RedisDep) -> None:
    ip = request.client.host if request.client else "unknown"
    await login_limiter.hit(redis, identity=f"{ip}:{payload.email}")
