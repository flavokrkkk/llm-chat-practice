import uuid
from typing import Annotated

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import ToolException, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolRuntime
from pydantic import Field

from app.agent.graph.pipeline import build_graph
from app.agent.graph.state import AgentContext
from app.agent.prompts.system import FALLBACK_REPLY
from tests.unit.agent.fakes import RecordingFakeModel
from tests.unit.agent.helpers import model_calling_tool, run_config


async def test_tool_is_called_with_user_id_from_context():
    received: list[uuid.UUID] = []

    @tool
    async def get_balance(runtime: ToolRuntime[AgentContext]) -> str:
        """Показать текущий баланс счёта клиента."""
        received.append(runtime.context.user_id)
        return "Баланс счёта: 1 000.00 ₸"

    llm = model_calling_tool(
        tool_name="get_balance", final_answer="Ваш баланс — 1 000.00 ₸."
    )

    graph = build_graph(llm=llm, tools=[get_balance], checkpointer=InMemorySaver())
    user_id = uuid.uuid4()

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Какой у меня баланс?", id="msg-1")]},
        config=run_config("chat-1"),
        context=AgentContext(user_id=user_id),
    )

    messages = result["messages"]

    assert [message.type for message in messages] == [
        "human",
        "ai",
        "tool",
        "ai",
    ]

    assert received == [user_id]

    assert messages[2].content == "Баланс счёта: 1 000.00 ₸"

    second_call = llm.calls[1]
    assert any(isinstance(m, ToolMessage) for m in second_call)


async def test_tool_exception_is_returned_to_model():
    @tool
    async def get_balance(runtime: ToolRuntime[AgentContext]) -> str:
        """Показать текущий баланс счёта клиента."""
        raise ToolException("Счёт клиента не найден")

    llm = model_calling_tool(
        tool_name="get_balance",
        final_answer="К сожалению, не удалось получить данные о счёте.",
    )
    graph = build_graph(llm=llm, tools=[get_balance], checkpointer=InMemorySaver())

    user_id = uuid.uuid4()

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Какой у меня баланс?", id="msg-1")]},
        config=run_config("chat-1"),
        context=AgentContext(user_id=user_id),
    )

    messages = result["messages"]

    assert [message.type for message in messages] == [
        "human",
        "ai",
        "tool",
        "ai",
    ]

    assert isinstance(messages[2], ToolMessage)

    assert messages[2].status == "error"

    assert "Счёт клиента не найден" in messages[2].content


async def test_unexpected_tool_error_propagates():
    @tool
    async def get_balance(runtime: ToolRuntime[AgentContext]) -> str:
        """Показать текущий баланс счёта клиента."""
        raise RuntimeError("bug in tool")

    llm = model_calling_tool(
        tool_name="get_balance",
        final_answer="К сожалению, не удалось получить данные о счёте.",
    )
    graph = build_graph(llm=llm, tools=[get_balance], checkpointer=InMemorySaver())

    user_id = uuid.uuid4()

    with pytest.raises(RuntimeError):
        await graph.ainvoke(
            {"messages": [HumanMessage("Какой у меня баланс?", id="msg-1")]},
            config=run_config("chat-1"),
            context=AgentContext(user_id=user_id),
        )


TRANSFERS_MESSAGE = "история переводов за последние 20 операций:\n\n1. 21.11.2026 20:02, исходящий, 50.00 ₸\n2. 03.11.2026 23:03, входящий, 20.00 ₸\n3. 03.11.2026 23:03, входящий, 20.00 ₸\n4. 03.11.2026 23:03, входящий, 20.00 ₸\n5. 03.11.2026 23:03, входящий, 20.00 ₸\n6. 03.11.2026 23:03, входящий, 20.00 ₸\n7. 03.11.2026 23:03, входящий, 20.00 ₸\n8. 03.11.2026 23:03, исходящий, 20.00 ₸\n9."


async def test_invalid_tool_args_are_reported_to_model():
    @tool
    async def get_history(
        runtime: ToolRuntime[AgentContext],
        limit: Annotated[int, Field(ge=1, le=20)] = 5,
    ) -> str:
        """Показать последние переводы клиента."""

        return TRANSFERS_MESSAGE

    llm = model_calling_tool(
        tool_name="get_history",
        final_answer="Не удалось получить историю",
        args={"limit": 1000},
    )

    graph = build_graph(llm=llm, tools=[get_history], checkpointer=InMemorySaver())

    user_id = uuid.uuid4()

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Покажи историю", id="msg-1")]},
        config=run_config("chat-1"),
        context=AgentContext(user_id=user_id),
    )

    messages = result["messages"]

    assert [m.type for m in messages] == ["human", "ai", "tool", "ai"]
    assert isinstance(messages[2], ToolMessage)
    assert messages[2].status == "error"
    assert "less than or equal to 20" in messages[2].content


async def test_text_tool_call_is_replaced_with_fallback():

    received: list[uuid.UUID] = []

    @tool
    async def get_balance(runtime: ToolRuntime[AgentContext]) -> str:
        """Показать текущий баланс счёта клиента."""

        received.append(runtime.context.user_id)

        return "Баланс счёта: 1 000.00 ₸"

    llm = RecordingFakeModel(
        messages=iter(
            [
                AIMessage('{"name": "get_balance", "arguments": {}}'),
            ]
        )
    )

    graph = build_graph(llm=llm, tools=[get_balance], checkpointer=InMemorySaver())

    user_id = uuid.uuid4()

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Какой у меня баланс?", id="msg-1")]},
        config=run_config("chat-1"),
        context=AgentContext(user_id=user_id),
    )

    messages = result["messages"]

    assert [message.type for message in messages] == ["human", "ai"]
    assert received == []
    assert messages[-1].text == FALLBACK_REPLY
