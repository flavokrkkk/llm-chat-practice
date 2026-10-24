import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.connection.postgres_connection import database
from app.api.router import v1_router
from app.core.clients.redis_client import redis_client
from app.core.error_handlers import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()

    yield

    await redis_client.close()

    await database.disconnect()


app = FastAPI(title="llm-chat", lifespan=lifespan)
app.include_router(v1_router, prefix="/api")
register_exception_handlers(app)
