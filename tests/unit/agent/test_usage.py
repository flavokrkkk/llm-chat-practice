import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.usage import sum_usage_after


def ai(text: str, tokens_in: int, tokens_out: int) -> AIMessage:
    return AIMessage(
        content=text,
        usage_metadata={
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": tokens_in + tokens_out,
        },
    )


def test_counts_only_messages_after_current_question():
    messages = [
        HumanMessage("Первый вопрос", id="q1"),
        ai("Первый ответ", 100, 10),
        HumanMessage("Какой у меня баланс?", id="q2"),
        ai("", 300, 20),
        ToolMessage("Баланс: 798.00 ₸", tool_call_id="call_1"),
        ai("Ваш баланс — 798.00 ₸", 350, 30),
    ]

    assert sum_usage_after(messages, "q2") == (650, 50)


def test_returns_none_when_no_usage_metadata():
    messages = [
        HumanMessage("Первый вопрос", id="q1"),
        AIMessage("Первый ответ"),
        HumanMessage("Какой у меня баланс?", id="q2"),
        AIMessage(""),
        ToolMessage("Баланс: 798.00 ₸", tool_call_id="call_1"),
        AIMessage("Ваш баланс — 798.00 ₸"),
    ]

    assert sum_usage_after(messages, "q2") == (None, None)


def test_raises_when_message_id_not_found():
    messages = [HumanMessage("Вопрос", id="q1")]

    with pytest.raises(RuntimeError):
        sum_usage_after(messages, "unknown")
