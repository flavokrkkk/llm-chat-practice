from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.config.config import settings


class DatabaseConnection:
    _engine = create_async_engine(
        url=settings.db.sqlalchemy_url,
        pool_size=settings.db.pool_size,
        pool_pre_ping=settings.db.pool_pre_ping,
        max_overflow=settings.db.max_overflow,
        echo=settings.db.echo,
    )

    @property
    async def session_factory(self) -> AsyncSession:
        return async_sessionmaker(bind=self._engine, expire_on_commit=False)

    async def session_scope(self):
        session = await self.session_factory
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def get_session(self):
        async with self.session_scope() as session:
            yield session
