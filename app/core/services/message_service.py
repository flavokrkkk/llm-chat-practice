import asyncio
import logging
import time
from datetime import datetime
from uuid import UUID

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph.state import AgentContext, AgentGraph
from app.core.repositories.chat_repository import ChatRepository
from app.core.repositories.message_repository import MessageRepository
from app.core.schemas.base import CursorPaginationResponse, PaginationResponse
from app.core.schemas.chat import ChatId
from app.core.schemas.message import MessageSchema
from app.infrastructure.config.config import AgentConfig
from app.infrastructure.errors.exceptions import ConflictError, LLMUnavailableError

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(
        self, session: AsyncSession, graph: AgentGraph, agent_config: AgentConfig
    ) -> None:
        self.message_repository = MessageRepository(session)
        self.chat_repository = ChatRepository(session)
        self.session = session
        self.graph = graph
        self.agent_config = agent_config

    async def _replay_or_conflict(self, message_id: UUID) -> MessageSchema:
        reply = await self.message_repository.find_reply_to(message_id)

        if reply is not None:
            return reply

        raise ConflictError("Message is still being processed")

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

            message, is_created = await self.message_repository.create_or_get_message(
                chat_id=chat_id,
                content=content,
                idempotency_key=idempotency_key,
            )

            if not is_created:
                return await self._replay_or_conflict(message_id=message.id)

        start_time = time.perf_counter()

        try:
            async with asyncio.timeout(self.agent_config.run_timeout_seconds):
                agent_response = await self.graph.ainvoke(
                    {"messages": [HumanMessage(content=content, id=str(message.id))]},
                    config={
                        "configurable": {"thread_id": str(chat_id)},
                        "recursion_limit": self.agent_config.recursion_limit,
                    },
                    context=AgentContext(user_id=user_id),
                )
        except TimeoutError as exc:
            raise LLMUnavailableError("LLM timeout") from exc

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        ai_message = agent_response["messages"][-1]
        usage = ai_message.usage_metadata

        tokens_in = usage["input_tokens"] if usage else None
        tokens_out = usage["output_tokens"] if usage else None

        logger.info(
            "agent reply: chat_id=%s tokens_in=%s tokens_out=%s latency_ms=%d",
            chat_id,
            tokens_in,
            tokens_out,
            latency_ms,
        )

        async with self.session.begin():
            assistant_message = await self.message_repository.create_reply(
                chat_id=chat_id,
                content=ai_message.text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                reply_to_id=message.id,
            )

        return assistant_message
