import logging

import asyncpg
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserSchema, TopUserStatsSchema
from app.core.clients.redis_client import RedisClient
from app.core.config import settings
from redis.exceptions import RedisError

CACHE_USER_STATS_KEY = "cache:top_users"
TTL_SECONDS = 60

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, connection: asyncpg.Connection, redis_client: RedisClient):
        self.user_repository = UserRepository(connection)
        self.redis_client = redis_client

    async def get_user_by_email(self, email: str) -> UserSchema:
        return await self.user_repository.get_user_by_email(email)

    async def get_user_stats(self) -> list[TopUserStatsSchema]:
        try:
            cached_top_users = await self.redis_client.get(CACHE_USER_STATS_KEY)
        except RedisError:
            # Кэш — оптимизация, при недоступности Redis не должны падать
            # основные сценарии: отчитываемся от кэш-ошибки и идем в БД.
            logger.warning(
                "Cache get failed for key=%s, fallback to database",
                CACHE_USER_STATS_KEY,
            )
            cached_top_users = None

        if cached_top_users is not None:
            return [
                TopUserStatsSchema.model_validate(item) for item in cached_top_users
            ]

        top_users = await self.user_repository.get_user_stats()

        top_users_for_cache = [
            top_user.model_dump(mode="json") for top_user in top_users
        ]

        try:
            await self.redis_client.set(
                CACHE_USER_STATS_KEY, top_users_for_cache, ttl=TTL_SECONDS
            )
        except RedisError:
            logger.warning(
                "Cache set failed for key=%s, continue without caching",
                CACHE_USER_STATS_KEY,
            )

        return top_users
