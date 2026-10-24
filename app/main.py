from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from app.database.connection.postgres_connection import database
from app.api.router import v1_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()

    yield

    await database.disconnect()


app = FastAPI(title="llm-chat", lifespan=lifespan)
app.include_router(v1_router, prefix="/api")
