import logging
from uuid import UUID

from fastapi import Depends, Header
from app.core.clients.redis_client import RedisClient, get_redis
from app.core.exceptions import RateLimitExceededError
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, limit: int = 10, window_seconds: int = 60):
        self.limit = limit
        self.window = window_seconds

    async def __call__(
        self,
        user_id: UUID = Header(..., alias="X-User-Id", description="ID отправителя"),
        redis: RedisClient = Depends(get_redis),
    ):
        key = f"rate_limit:messages:{user_id}"

        try:
            current = await redis.redis.incr(key)

            if current == 1:
                await redis.redis.expire(key, self.window)
        except RedisError:
            # Fail-open: при недоступности Redis не блокируем запросы,
            # чтобы не превратить сбой инфраструктуры в полный даун для клиентов.
            logger.warning(
                "Rate limiter backend error, allow request. key=%s", key, exc_info=True
            )
            return None

        if current > self.limit:
            raise RateLimitExceededError("Too Many Requests: Rate limit exceeded")
