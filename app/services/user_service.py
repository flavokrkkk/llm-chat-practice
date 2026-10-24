import asyncpg
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserSchema, TopUserStatsSchema


class UserService:
    def __init__(self, connection: asyncpg.Connection):
        self.user_repository = UserRepository(connection)

    async def get_user_by_email(self, email: str) -> UserSchema:
        return await self.user_repository.get_user_by_email(email)

    async def get_user_stats(self) -> list[TopUserStatsSchema]:
        return await self.user_repository.get_user_stats()
