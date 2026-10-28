from decimal import Decimal

import asyncpg

from app.schemas.transfer import TransferSchema
from app.schemas.user import UserId


class TransferRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def create_transfer(
        self, to_user_id: UserId, from_user_id: UserId, amount: Decimal
    ) -> TransferSchema:
        row = await self.connection.fetchrow(
            """
            INSERT INTO transfers (from_user_id, to_user_id, amount) 
            VALUES ($1, $2, $3)
            RETURNING id, from_user_id, to_user_id, amount, created_at
            """,
            from_user_id,
            to_user_id,
            amount,
        )

        return TransferSchema.model_validate(row)
