import enum


class MessageRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class OutboxEventType(enum.StrEnum):
    TRANSFER_COMPLETED = "transfer.completed"


class PendingActionKind(enum.StrEnum):
    TRANSFER = "transfer"


class PendingActionStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    DONE = "done"
