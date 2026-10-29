from redis.asyncio import Redis

from app.infrastructure.config.config import RedisConfig


class RedisConnection:
    def __init__(self, config: RedisConfig) -> None:
        self.redis = Redis.from_url(str(config.url), decode_responses=True)

    async def close(self) -> None:
        await self.redis.aclose()
