from fastapi import Depends, HTTPException, Header
from uuid import UUID
from app.core.clients.redis_client import RedisClient, get_redis


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
        current = await redis.redis.incr(key)

        if current == 1:
            await redis.redis.expire(key, self.window)

        if current > self.limit:
            raise HTTPException(
                status_code=429, detail="Too Many Requests: Rate limit exceeded"
            )
