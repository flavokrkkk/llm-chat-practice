import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    def __init__(self, redis_url: str = settings.redis_url) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)

    async def set(
        self, key: str, value: Any, ttl: int = settings.cache_ttl_seconds
    ) -> None:
        json_data = json.dumps(value, default=str)
        await self.redis.set(key, json_data, ex=ttl)

    async def get(self, key: str) -> Any | None:
        data = await self.redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def close(self) -> None:
        await self.redis.close()


redis_client = RedisClient(settings.redis_url)


def get_redis() -> RedisClient:
    return redis_client
