import asyncpg
from app.schemas.user import UserSchema, TopUserStatsSchema


class UserRepository:

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_user_by_email(self, email: str):
        raw = await self.connection.fetchrow(
            "SELECT id, email, balance, created_at from users WHERE lower(email) = $1",
            email.lower(),
        )

        return UserSchema.model_validate(raw)

    async def get_user_stats(self) -> list[TopUserStatsSchema]:
        rows = await self.connection.fetch(""" 
            SELECT
                u.id AS user_id,
                u.email,
                u.balance,
                u.created_at,
                COUNT(m.id) AS messages_count
            FROM users u 
            INNER JOIN chats c ON c.user_id = u.id
            INNER JOIN messages m ON m.chat_id = c.id
            WHERE m.created_at >= NOW() - INTERVAL '7 days'
            GROUP BY u.id
            HAVING COUNT(m.id) > 0
            ORDER BY messages_count DESC
            LIMIT 10;
            """)

        return [TopUserStatsSchema.model_validate(dict(row)) for row in rows]
