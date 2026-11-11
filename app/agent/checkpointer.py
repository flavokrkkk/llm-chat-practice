from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from app.infrastructure.config.config import CheckpointerConfig, DatabaseConfig


@asynccontextmanager
async def create_checkpointer(
    db: DatabaseConfig, config: CheckpointerConfig
) -> AsyncIterator[AsyncPostgresSaver]:
    """Пул psycopg + Postgres-чекпоинтер LangGraph на время жизни приложения."""
    async with AsyncConnectionPool(
        conninfo=db.psycopg_url,
        min_size=config.pool_min_size,
        max_size=config.pool_max_size,
        open=False,
        connection_class=AsyncConnection[DictRow],
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        yield checkpointer
