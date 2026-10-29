import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.router import v1_router
from app.infrastructure.config.config import settings
from app.infrastructure.database.connection.postgres_connection import (
    DatabaseConnection,
)
from app.infrastructure.errors.error_handlers import register_exception_handlers
from app.infrastructure.redis.cache import RedisCache
from app.infrastructure.redis.connection import RedisConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:

    async with AsyncExitStack() as stack:
        db = DatabaseConnection(settings.db)
        stack.push_async_callback(db.close)
        app.state.db_connection = db

        redis = RedisConnection(settings.redis)
        stack.push_async_callback(redis.close)
        app.state.redis_connection = redis

        app.state.cache = RedisCache(
            redis=redis.redis, default_ttl=settings.redis.cache_ttl_seconds
        )
        yield


app = FastAPI(title="llm-chat", lifespan=lifespan)
app.include_router(v1_router, prefix="/api")
register_exception_handlers(app)
