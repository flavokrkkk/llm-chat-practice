from sqlalchemy import select

from app.core.schemas.chat import ChatId, ChatSchema, ChatWithMessagesSchema
from app.core.schemas.user import UserId
from app.infrastructure.database.models.chat import Chat
from app.infrastructure.errors.exceptions import NotFoundError

from .base_repository import SqlAlchemyRepository


class ChatRepository(SqlAlchemyRepository):
    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        query = select(Chat).where(Chat.id == chat_id)

        result = await self.session.scalar(query)

        if result is None:
            raise NotFoundError("Chat not found")

        return ChatSchema.model_validate(result)

    async def get_user_chats(self, user_id: UserId) -> list[ChatWithMessagesSchema]:
        pass
        # query = (
        #     select(Chat).outerjoin()
        # )

        # rows = await self.connection.fetch(
        #     """
        #         SELECT
        #             c.id,
        #             c.user_id,
        #             c.title,
        #             c.created_at,
        #             COALESCE(
        #                 jsonb_agg(
        #                     jsonb_build_object(
        #                         'id', m.id,
        #                         'content', m.content,
        #                         'role', m.role,
        #                         'chat_id', m.chat_id,
        #                         'idempotency_key', m.idempotency_key,
        #                         'created_at', m.created_at
        #                     )
        #                 ) FILTER (WHERE m.id IS NOT NULL),
        #                 '[]'::jsonb
        #             ) AS last_messages
        #         FROM chats c
        #         LEFT JOIN LATERAL (
        #         -- Этот подзапрос выполняется отдельно ДЛЯ КАЖДОГО чата
        #         SELECT id, content, role, chat_id, idempotency_key, created_at
        #         FROM messages
        #         WHERE chat_id = c.id
        #         ORDER BY created_at DESC, id DESC
        #         LIMIT 3
        #         ) m ON TRUE
        #         WHERE c.user_id = $1
        #         GROUP BY c.id, c.title, c.user_id, c.created_at;
        #     """,
        #     user_id,
        # )

        # return [ChatWithMessagesSchema.model_validate(dict(row)) for row in rows]
