import asyncpg
from app.schemas.chat import ChatId, ChatSchema


class ChatRepository:

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        row = await self.connection.fetchrow(
            "SELECT id, user_id, title, created_at FROM chats WHERE id = $1", chat_id
        )

        chat = ChatSchema.model_validate(row)
        return chat
