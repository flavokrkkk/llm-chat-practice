import asyncpg
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatId, ChatSchema


class ChatService:
    def __init__(self, connection: asyncpg.Connection):
        self.chat_reposiotory = ChatRepository(connection)

    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        return await self.chat_reposiotory.get_chat_by_id(chat_id)
