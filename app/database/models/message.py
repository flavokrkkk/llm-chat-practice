import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, text

from app.database.models.base import Base, CreatedAtMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.database.models.chat import Chat


class MessageRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_chat_keyset", "chat_id", "created_at", "id"),
        Index(
            "ix_messages_user_role",
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
    )

    content: Mapped[str] = mapped_column(Text)
    chat_id: Mapped[UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="role",
            native_enum=False,
            length=10,
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)

    chat: Mapped["Chat"] = relationship(back_populates="messages")
