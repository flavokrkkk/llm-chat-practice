import asyncpg
from app.repositories.message_repository import MessageRepository
from app.repositories.chat_repository import ChatRepository
from typing import Optional
from datetime import datetime

from app.schemas.chat import ChatId
from app.schemas.message import MessageSchema
from app.schemas.base import PaginationResponse


class MessageService:
    def __init__(self, connection: asyncpg.Connection):
        self.message_repository = MessageRepository(connection)
        self.chat_repository = ChatRepository(connection)

    async def get_chat_messages(
        self, chat_id: ChatId, limit: int
    ) -> list[MessageSchema]:
        return await self.message_repository.get_chat_messages(chat_id, limit)

    async def get_chat_messages_offset(
        self, chat_id: ChatId, limit: int, offset: int
    ) -> PaginationResponse:
        return await self.message_repository.get_chat_messages_offset(
            chat_id=chat_id, limit=limit, offset=offset
        )

    async def get_chat_messages_keyset(
        self,
        chat_id: ChatId,
        limit: int,
        cursor_id: int,
        cursor_created_at: Optional[datetime] = None,
    ) -> PaginationResponse:
        return await self.message_repository.get_chat_messages_keyset(
            chat_id=chat_id,
            limit=limit,
            cursor_id=cursor_id,
            cursor_created_at=cursor_created_at,
        )
