from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
