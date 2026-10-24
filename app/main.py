from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from app.database.connection.postgres_connection import database
from app.api.router import v1_router
from app.core.clients.redis_client import redis_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()

    yield

    await redis_client.close()

    await database.disconnect()


app = FastAPI(title="llm-chat", lifespan=lifespan)
app.include_router(v1_router, prefix="/api")
