from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert

from app.core.schemas.base import CursorPaginationResponse, PaginationResponse
from app.core.schemas.chat import ChatId
from app.core.schemas.message import MessageRole, MessageSchema
from app.infrastructure.database.models import Message
from app.infrastructure.errors.exceptions import NotFoundError

from .base_repository import SqlAlchemyRepository


class MessageRepository(SqlAlchemyRepository):
    async def get_chat_messages(
        self, chat_id: ChatId, limit: int
    ) -> list[MessageSchema]:

        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )

        result = await self.session.scalars(query)

        messages = [MessageSchema.model_validate(x) for x in result]

        return messages

    async def get_chat_messages_offset(
        self, chat_id: ChatId, limit: int, offset: int
    ) -> PaginationResponse:

        total_query = select(func.count(Message.id)).where(Message.chat_id == chat_id)

        total = (await self.session.execute(total_query)).scalar_one()

        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .offset(offset)
        )

        rows = await self.session.scalars(query)

        return PaginationResponse(
            items=[MessageSchema.model_validate(x) for x in rows],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_chat_messages_keyset(
        self,
        chat_id: ChatId,
        limit: int,
        cursor_id: Optional[UUID] = None,
        cursor_created_at: Optional[datetime] = None,
    ) -> CursorPaginationResponse:

        final_query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit + 1)
        )

        if cursor_created_at is not None and cursor_id is not None:
            final_query = final_query.where(
                tuple_(Message.created_at, Message.id)
                < tuple_(cursor_created_at, cursor_id)
            )

        rows = (await self.session.scalars(final_query)).all()

        has_more = len(rows) > limit

        items = [MessageSchema.model_validate(x) for x in rows[:limit]]

        next_created_at = None
        next_id = None

        if has_more:
            next_created_at = items[-1].created_at
            next_id = items[-1].id

        return CursorPaginationResponse(
            items=items, next_created_at=next_created_at, next_id=next_id, limit=limit
        )

    async def create_message(
        self,
        chat_id: ChatId,
        role: MessageRole,
        content: str,
        idempotency_key: str | None,
    ) -> MessageSchema:

        query = (
            insert(Message)
            .values(
                chat_id=chat_id,
                role=role,
                content=content,
                idempotency_key=idempotency_key,
            )
            .on_conflict_do_nothing(
                index_elements=[Message.chat_id, Message.idempotency_key]
            )
            .returning(Message)
        )

        row = await self.session.scalar(query)

        if row is None:
            conflict_query = select(Message).where(
                Message.chat_id == chat_id, Message.idempotency_key == idempotency_key
            )

            message = await self.session.scalar(conflict_query)

            row = message

        if row is None:
            raise NotFoundError("Message not found")

        return MessageSchema.model_validate(row)
