from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infrastructure.config.config import DatabaseConfig


class DatabaseConnection:
    def __init__(self, config: DatabaseConfig) -> None:
        self._engine = create_async_engine(
            url=config.sqlalchemy_url,
            pool_size=config.pool_size,
            pool_pre_ping=config.pool_pre_ping,
            max_overflow=config.max_overflow,
            echo=config.echo,
        )

        self.session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def close(self) -> None:
        await self._engine.dispose()
