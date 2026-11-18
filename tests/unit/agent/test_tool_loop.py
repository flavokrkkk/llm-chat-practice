import uuid

import pytest
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import ToolException, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolRuntime

from app.agent.graph.pipeline import build_graph
from app.agent.graph.state import AgentContext
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
