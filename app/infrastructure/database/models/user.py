from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, CreatedAtMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.chat import Chat
    from app.infrastructure.database.models.pending_action import PendingAction
    from app.infrastructure.database.models.refresh_token import RefreshToken
    from app.infrastructure.database.models.transfer import Transfer


class User(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="balance_non_negative"),
        Index("ix_users_lower_email", text("lower(email)"), unique=True),
    )

    email: Mapped[str]
    full_name: Mapped[str]
    balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 2),
        server_default=text("0"),
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    chats: Mapped[list["Chat"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
    pending_actions: Mapped[list["PendingAction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
    sent_transfers: Mapped[list["Transfer"]] = relationship(
        foreign_keys="Transfer.from_user_id",
        back_populates="from_user",
        passive_deletes="all",
        lazy="raise",
    )
    received_transfers: Mapped[list["Transfer"]] = relationship(
        foreign_keys="Transfer.to_user_id",
        back_populates="to_user",
        passive_deletes="all",
        lazy="raise",
    )
