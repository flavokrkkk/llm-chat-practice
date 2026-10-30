from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.chat_repository import ChatRepository
from app.core.schemas.chat import ChatId, ChatSchema, ChatWithMessagesSchema
from app.core.schemas.user import UserId


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.chat_repository = ChatRepository(session)

    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        # учитывать user_id
        return await self.chat_repository.get_chat_by_id(chat_id)

    async def get_user_chats(self, user_id: UserId) -> list[ChatWithMessagesSchema]:
        return await self.chat_repository.get_user_chats(user_id)
