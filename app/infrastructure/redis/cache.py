import json
from typing import Any

from redis.asyncio import Redis


class RedisCache:
    def __init__(
        self,
        redis: Redis,
        default_ttl: int,
    ) -> None:
        self._redis = redis
        self._default_ttl = default_ttl

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl is None:
            ttl = self._default_ttl

        json_data = json.dumps(value, default=str)
        await self._redis.set(key, json_data, ex=ttl)

    async def get(self, key: str) -> Any | None:
        data = await self._redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)
