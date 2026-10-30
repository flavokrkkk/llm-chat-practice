from sqlalchemy import func, literal_column, select, true
from sqlalchemy.dialects.postgresql import JSONB

from app.core.schemas.chat import ChatId, ChatSchema, ChatWithMessagesSchema
from app.core.schemas.user import UserId
from app.infrastructure.database.models.chat import Chat
from app.infrastructure.database.models.message import Message
from app.infrastructure.errors.exceptions import NotFoundError

from .base_repository import SqlAlchemyRepository


class ChatRepository(SqlAlchemyRepository):
    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        result = await self.session.get(Chat, chat_id)

        if result is None:
            raise NotFoundError("Chat not found")

        return ChatSchema.model_validate(result)

    async def get_user_chats(self, user_id: UserId) -> list[ChatWithMessagesSchema]:
        recent_messages = (
            select(
                Message.id,
                Message.content,
                Message.role,
                Message.chat_id,
                Message.idempotency_key,
                Message.created_at,
            )
            .where(Message.chat_id == Chat.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(3)
            .lateral("recent_messages")
        )

        last_messages = func.coalesce(
            func.jsonb_agg(
                func.jsonb_build_object(
                    "id",
                    recent_messages.c.id,
                    "content",
                    recent_messages.c.content,
                    "role",
                    recent_messages.c.role,
                    "chat_id",
                    recent_messages.c.chat_id,
                    "idempotency_key",
                    recent_messages.c.idempotency_key,
                    "created_at",
                    recent_messages.c.created_at,
                )
            ).filter(recent_messages.c.id.is_not(None)),
            literal_column("'[]'::jsonb"),
            type_=JSONB,
        ).label("last_messages")

        stmt = (
            select(
                Chat.id,
                Chat.user_id,
                Chat.title,
                Chat.created_at,
                last_messages,
            )
            .outerjoin(recent_messages, true())
            .where(Chat.user_id == user_id)
            .group_by(Chat.id)
            .order_by(Chat.created_at.desc())
        )

        rows = (await self.session.execute(stmt)).mappings()

        return [ChatWithMessagesSchema.model_validate(row) for row in rows]
