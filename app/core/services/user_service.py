import logging

from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.user_repository import UserRepository
from app.core.schemas.user import TopUserStatsSchema, UserSchema
from app.infrastructure.redis.cache import RedisCache

CACHE_USER_STATS_KEY = "cache:top_users"
STATS_TTL_SECONDS = 60

TOP_USERS_ADAPTER = TypeAdapter(list[TopUserStatsSchema])


logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: AsyncSession, cache: RedisCache) -> None:
        self.user_repository = UserRepository(session)
        self.cache = cache

    async def get_user_by_email(self, email: str) -> UserSchema:
        return await self.user_repository.get_user_by_email(email)

    async def get_user_stats(self) -> list[TopUserStatsSchema]:
        cached_top_users = await self.cache.get(CACHE_USER_STATS_KEY)

        if cached_top_users is not None:
            try:
                return TOP_USERS_ADAPTER.validate_python(cached_top_users)

            except ValidationError:
                logger.warning(
                    "Cached value for key=%s does not match TopUserStatsSchema, "
                    "deleting it and falling back to database",
                    CACHE_USER_STATS_KEY,
                    exc_info=True,
                )
                await self.cache.delete(key=CACHE_USER_STATS_KEY)

        top_users = await self.user_repository.get_user_stats()

        top_users_for_cache = TOP_USERS_ADAPTER.dump_python(top_users, mode="json")

        await self.cache.set(
            CACHE_USER_STATS_KEY, top_users_for_cache, ttl=STATS_TTL_SECONDS
        )

        return top_users
