from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.chat_repository import ChatRepository
from app.core.repositories.message_repository import MessageRepository
from app.core.schemas.base import CursorPaginationResponse, PaginationResponse
from app.core.schemas.chat import ChatId
from app.core.schemas.message import MessageRole, MessageSchema


class MessageService:
    def __init__(self, session: AsyncSession) -> None:
        self.message_repository = MessageRepository(session)
        self.chat_repository = ChatRepository(session)
        self.session = session

    async def get_chat_messages(
        self, user_id: UUID, chat_id: ChatId, limit: int
    ) -> list[MessageSchema]:
        return await self.message_repository.get_chat_messages(
            user_id=user_id, chat_id=chat_id, limit=limit
        )

    async def get_chat_messages_offset(
        self, user_id: UUID, chat_id: ChatId, limit: int, offset: int
    ) -> PaginationResponse:
        return await self.message_repository.get_chat_messages_offset(
            user_id=user_id, chat_id=chat_id, limit=limit, offset=offset
        )

    async def get_chat_messages_keyset(
        self,
        user_id: UUID,
        chat_id: ChatId,
        limit: int,
        cursor_id: UUID | None = None,
        cursor_created_at: datetime | None = None,
    ) -> CursorPaginationResponse:
        return await self.message_repository.get_chat_messages_keyset(
            user_id=user_id,
            chat_id=chat_id,
            limit=limit,
            cursor_id=cursor_id,
            cursor_created_at=cursor_created_at,
        )

    async def create_chat_message(
        self,
        user_id: UUID,
        chat_id: ChatId,
        content: str,
        idempotency_key: str | None,
    ) -> MessageSchema:
        async with self.session.begin():
            await self.chat_repository.get_chat_by_id(chat_id, user_id)

            return await self.message_repository.create_message(
                chat_id=chat_id,
                role=MessageRole.USER,
                content=content,
                idempotency_key=idempotency_key,
            )
