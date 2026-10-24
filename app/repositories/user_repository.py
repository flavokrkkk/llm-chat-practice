import asyncpg
from app.schemas.user import UserSchema


class UserRepository:

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_user_by_email(self, email: str):
        raw = await self.connection.fetchrow(
            "SELECT id, email, balance, created_at from users WHERE lower(email) = $1",
            email.lower(),
        )

        return UserSchema.model_validate(raw)
