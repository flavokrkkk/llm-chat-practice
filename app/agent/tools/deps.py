from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.redis.cache import RedisCache


@dataclass(frozen=True)
class ToolDeps:
    """Долгоживущие зависимости инструментов агента."""

    session_factory: async_sessionmaker[AsyncSession]
    cache: RedisCache
