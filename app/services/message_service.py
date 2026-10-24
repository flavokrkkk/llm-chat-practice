import asyncpg
from app.repositories.message_repository import MessageRepository
from app.repositories.chat_repository import ChatRepository

from app.schemas.chat import ChatId
from app.schemas.message import MessageSchema


class MessageService:
    def __init__(self, connection: asyncpg.Connection):
        self.message_repository = MessageRepository(connection)
        self.chat_repository = ChatRepository(connection)

    async def get_chat_messages(
        self, chat_id: ChatId, limit: int
    ) -> list[MessageSchema]:
        return await self.message_repository.get_chat_messages(chat_id, limit)
