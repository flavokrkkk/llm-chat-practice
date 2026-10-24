import asyncpg
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatId, ChatSchema, ChatWithMessagesSchema
from app.schemas.user import UserId


class ChatService:
    def __init__(self, connection: asyncpg.Connection):
        self.chat_reposiotory = ChatRepository(connection)

    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        return await self.chat_reposiotory.get_chat_by_id(chat_id)

    async def get_user_chats(self, user_id: UserId) -> list[ChatWithMessagesSchema]:
        return await self.chat_reposiotory.get_user_chats(user_id)
