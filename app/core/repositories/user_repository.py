from decimal import Decimal

import asyncpg

from app.core.schemas.user import TopUserStatsSchema, UserId, UserSchema
from app.infrastructure.errors.exceptions import NotFoundError


class UserRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_user_by_id(self, user_id: UserId) -> UserSchema:
        row = await self.connection.fetchrow(
            "SELECT id, email, balance, created_at FROM users WHERE id = $1", user_id
        )

        if row is None:
            raise NotFoundError("User not found")

        return UserSchema.model_validate(row)

    async def get_user_by_email(self, email: str):
        raw = await self.connection.fetchrow(
            "SELECT id, email, balance, created_at from users WHERE lower(email) = $1",
            email.lower(),
        )

        if raw is None:
            raise NotFoundError("User not found")

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

    async def get_balance_for_update(self, user_id: UserId) -> Decimal:
        val = await self.connection.fetchval(
            "SELECT balance FROM users WHERE id = $1 FOR UPDATE", user_id
        )

        if val is None:
            raise NotFoundError("User not found")

        return val

    async def get_balance(self, user_id: UserId) -> Decimal:
        val = await self.connection.fetchval(
            "SELECT balance FROM users WHERE id = $1", user_id
        )

        if val is None:
            raise NotFoundError("User not found")

        return val

    async def deduct_balance(self, user_id: UserId, amount: Decimal):
        return await self.connection.execute(
            "UPDATE users SET balance = balance - $1 WHERE id = $2",
            amount,
            user_id,
        )

    async def add_balance(self, user_id: UserId, amount: Decimal):
        return await self.connection.execute(
            "UPDATE users SET balance = balance + $1 WHERE id = $2",
            amount,
            user_id,
        )

    async def deduct_balance_atomic(self, user_id: UserId, amount: Decimal) -> bool:
        updated_id = await self.connection.fetchval(
            """
            UPDATE users 
            SET balance = balance - $1 
            WHERE id = $2 AND balance >= $1
            RETURNING id;
            """,
            amount,
            user_id,
        )

        return updated_id is not None
