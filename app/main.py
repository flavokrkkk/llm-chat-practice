from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.connection.postgres_connection import database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()

    yield

    await database.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health():

    return {"status": "OK"}
