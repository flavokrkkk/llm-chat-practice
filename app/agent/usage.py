from typing import Sequence

from langchain_core.messages import AIMessage, AnyMessage


def sum_usage_after(
    messages: Sequence[AnyMessage], message_id: str
) -> tuple[int | None, int | None]:
    """Сумма токенов всех ответов модели после сообщения с этим id."""

    start = next((i for i, m in enumerate(messages) if m.id == message_id), None)

    if start is None:
        raise RuntimeError(f"Message {message_id} not found in graph state")

    ai_messages = [m for m in messages[start + 1 :] if isinstance(m, AIMessage)]

    usages = [m.usage_metadata for m in ai_messages if m.usage_metadata is not None]

    if not usages:
        return None, None

    tokens_in = sum(u["input_tokens"] for u in usages)
    tokens_out = sum(u["output_tokens"] for u in usages)

    return tokens_in, tokens_out
