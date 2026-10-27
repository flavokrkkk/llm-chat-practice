from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.database.models.message import Message
    from app.database.models.user import User


class Chat(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "chats"

    title: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user: Mapped["User"] = relationship(back_populates="chats")
