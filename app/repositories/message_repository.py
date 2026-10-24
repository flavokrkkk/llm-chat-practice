import asyncpg

from app.schemas.message import MessageSchema
from app.schemas.chat import ChatId


class MessageRepository:

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_chat_messages(
        self, chat_id: ChatId, limit: int
    ) -> list[MessageSchema]:
        rows = await self.connection.fetch(
            """ 
            SELECT id, chat_id, role, content, idempotency_key, created_at
            FROM messages
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            chat_id,
            limit,
        )

        messages = [MessageSchema.model_validate(x) for x in rows]

        return messages
