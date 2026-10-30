from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import (
    Base,
    CreatedAtMixin,
    UUIDPkMixin,
    str_enum,
)
from app.utils.enums import MessageRole

if TYPE_CHECKING:
    from app.infrastructure.database.models.chat import Chat


class Message(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_chat_id_created_at_id", "chat_id", "created_at", "id"),
        Index(
            "ix_messages_chat_id_created_at_user",
            "chat_id",
            "created_at",
            postgresql_where=text("role = 'user'"),
        ),
        Index(
            "ix_messages_content_trgm",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
        ),
        UniqueConstraint(
            "chat_id", "idempotency_key", name="uq_messages_chat_idempotency"
        ),
        CheckConstraint("tokens_in >= 0", name="tokens_in_non_negative"),
        CheckConstraint("tokens_out >= 0", name="tokens_out_non_negative"),
        CheckConstraint("latency_ms >= 0", name="latency_ms_non_negative"),
    )

    content: Mapped[str] = mapped_column(Text)
    chat_id: Mapped[UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(
        str_enum(MessageRole, name="role", length=10)
    )
    tokens_in: Mapped[int | None]
    tokens_out: Mapped[int | None]
    latency_ms: Mapped[int | None]
    idempotency_key: Mapped[str | None] = mapped_column(String(255))

    chat: Mapped["Chat"] = relationship(back_populates="messages", lazy="raise")
