import asyncpg
from app.core.exceptions import NotFoundError
from app.schemas.chat import ChatId, ChatSchema, ChatWithMessagesSchema
from app.schemas.user import UserId


class ChatRepository:

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_chat_by_id(self, chat_id: ChatId) -> ChatSchema:
        row = await self.connection.fetchrow(
            "SELECT id, user_id, title, created_at FROM chats WHERE id = $1", chat_id
        )

        if row is None:
            raise NotFoundError("Chat not found")

        chat = ChatSchema.model_validate(row)
        return chat

    async def get_user_chats(self, user_id: UserId) -> list[ChatWithMessagesSchema]:
        rows = await self.connection.fetch(
            """
                SELECT
                    c.id,
                    c.user_id,
                    c.title,
                    c.created_at,
                    COALESCE(
                        jsonb_agg(
                            jsonb_build_object(
                                'id', m.id,
                                'content', m.content,
                                'role', m.role,
                                'chat_id', m.chat_id,
                                'idempotency_key', m.idempotency_key,
                                'created_at', m.created_at
                            )
                        ) FILTER (WHERE m.id IS NOT NULL), 
                        '[]'::jsonb
                    ) AS last_messages
                FROM chats c
                LEFT JOIN LATERAL (
                -- Этот подзапрос выполняется отдельно ДЛЯ КАЖДОГО чата
                SELECT id, content, role, chat_id, idempotency_key, created_at
                FROM messages
                WHERE chat_id = c.id
                ORDER BY created_at DESC, id DESC
                LIMIT 3
                ) m ON TRUE
                WHERE c.user_id = $1
                GROUP BY c.id, c.title, c.user_id, c.created_at;
            """,
            user_id,
        )

        return [ChatWithMessagesSchema.model_validate(dict(row)) for row in rows]
