import logging
from json import JSONDecodeError, dumps, loads
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


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

        json_data = dumps(value, default=str)

        try:
            await self._redis.set(key, json_data, ex=ttl)
        except RedisError:
            logger.warning(
                "Cache set failed for key=%s, continue without caching",
                key,
                exc_info=True,
            )

    async def get(self, key: str) -> Any | None:
        try:
            data = await self._redis.get(key)
        except RedisError:
            logger.warning(
                "Cache get failed for key=%s, treating as cache miss",
                key,
                exc_info=True,
            )
            return None

        if data is None:
            return None

        try:
            return loads(data)
        except JSONDecodeError:
            logger.warning(
                "Cache value for key=%s is not valid JSON, deleting it",
                key,
                exc_info=True,
            )
            await self.delete(key)
            return None

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except RedisError:
            logger.error(
                "Cache delete failed for key=%s, stale value may remain until TTL expires",
                key,
                exc_info=True,
            )
