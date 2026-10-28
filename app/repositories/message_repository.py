from datetime import datetime
from typing import Optional
from uuid import UUID

import asyncpg

from app.core.exceptions import NotFoundError
from app.schemas.base import CursorPaginationResponse, PaginationResponse
from app.schemas.chat import ChatId
from app.schemas.message import MessageRole, MessageSchema


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

    async def get_chat_messages_offset(
        self, chat_id: ChatId, limit: int, offset: int
    ) -> PaginationResponse:
        total = await self.connection.fetchval(
            "SELECT COUNT(*) from messages WHERE chat_id = $1", chat_id
        )

        rows = await self.connection.fetch(
            """
            SELECT id, chat_id, role, content, idempotency_key, created_at
            FROM messages
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            chat_id,
            limit,
            offset,
        )

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

        base_query = """
            SELECT id, chat_id, role, content, idempotency_key, created_at
            FROM messages 
            WHERE chat_id = $1
        """

        args = [chat_id]

        if cursor_created_at is not None and cursor_id is not None:
            args.append(cursor_created_at)
            args.append(cursor_id)

            args.append(limit)

            final_query = f"""
            {base_query}
            AND (created_at, id) < ($2::timestamptz, $3::uuid)
            ORDER BY created_at DESC, id DESC 
            LIMIT $4
            """

        else:
            args.append(limit)

            final_query = f"""
            {base_query}
            ORDER BY created_at DESC, id DESC 
            LIMIT $2
            """

        rows = await self.connection.fetch(final_query, *args)

        items = [MessageSchema.model_validate(x) for x in rows]

        next_created_at = None
        next_id = None

        if len(items) == limit:
            next_created_at = items[-1].created_at
            next_id = items[-1].id

        return CursorPaginationResponse(
            items=items, next_created_at=next_created_at, next_id=next_id, limit=limit
        )

    async def create_message(
        self, chatd_id: ChatId, role: MessageRole, content: str, idempotency_key: str
    ):
        row = await self.connection.fetchrow(
            """
            INSERT INTO messages (chat_id, role, content, idempotency_key)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (chat_id, idempotency_key) DO NOTHING
            RETURNING id, chat_id, role, content, idempotency_key, created_at;
            """,
            chatd_id,
            role,
            content,
            idempotency_key,
        )

        if row is None:
            message = await self.connection.fetchrow(
                "SELECT * FROM messages WHERE chat_id = $1 AND idempotency_key = $2",
                chatd_id,
                idempotency_key,
            )

            row = message

        if row is None:
            raise NotFoundError("Message not found")

        return MessageSchema.model_validate(row)
