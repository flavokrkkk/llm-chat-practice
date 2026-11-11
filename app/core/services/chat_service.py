from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.chat_repository import ChatRepository
from app.core.schemas.chat import ChatId, ChatSchema, ChatWithMessagesSchema


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.chat_repository = ChatRepository(session)
        self.session = session

    async def get_chat_by_id(self, chat_id: ChatId, user_id: UUID) -> ChatSchema:
        return await self.chat_repository.get_chat_by_id(chat_id, user_id)

    async def get_user_chats(self, user_id: UUID) -> list[ChatWithMessagesSchema]:
        return await self.chat_repository.get_user_chats(user_id)

    async def create_chat(self, user_id: UUID, title: str) -> ChatSchema:
        async with self.session.begin():
            return await self.chat_repository.create_chat(user_id=user_id, title=title)
