import asyncpg
from typing import AsyncGenerator
from app.core.config import settings


class Postgres:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.database_url, min_size=10, max_size=60
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if self.pool is None:
            raise RuntimeError(
                "Database pool is not initialized. Did you forget to call connect()?"
            )

        async with self.pool.acquire() as connection:
            yield connection


database = Postgres(settings.database_url)
