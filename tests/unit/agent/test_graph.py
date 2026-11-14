import uuid

import httpx
import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from ollama import ResponseError

from app.agent.graph.pipeline import build_graph
from app.agent.graph.state import AgentContext
from app.agent.prompts.system import get_system_prompt
from app.infrastructure.errors.exceptions import LLMUnavailableError
from tests.unit.agent.fakes import FailingFakeModel


def run_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


async def test_reply_is_added_and_system_prompt_is_not_saved(graph):
    result = await graph.ainvoke(
        {"messages": [HumanMessage("Привет", id="msg-1")]},
        config=run_config("chat-1"),
        context=AgentContext(user_id=uuid.uuid4()),
    )

    assert [m.type for m in result["messages"]] == ["human", "ai"]
    assert result["messages"][-1].content == "Первый ответ"


async def test_system_prompt_is_sent_to_model_first(graph, fake_llm):
    await graph.ainvoke(
        {"messages": [HumanMessage("Привет", id="msg-1")]},
        config=run_config("chat-2"),
        context=AgentContext(user_id=uuid.uuid4()),
    )
    sent = fake_llm.calls[0]
    assert isinstance(sent[0], SystemMessage)
    assert sent[0].content == get_system_prompt()
    assert sent[1].content == "Привет"


async def test_history_accumulates_in_same_thread(graph):
    config = run_config("chat-1")
    context = AgentContext(user_id=uuid.uuid4())

    await graph.ainvoke(
        {"messages": [HumanMessage("Первый вопрос", id="msg-1")]},
        config=config,
        context=context,
    )

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Второй вопрос", id="msg-2")]},
        config=config,
        context=context,
    )

    assert [message.type for message in result["messages"]] == [
        "human",
        "ai",
        "human",
        "ai",
    ]


async def test_threads_are_isolated(graph):
    context = AgentContext(user_id=uuid.uuid4())

    await graph.ainvoke(
        {"messages": [HumanMessage("Вопрос в чате A", id="msg-a")]},
        config=run_config("chat-a"),
        context=context,
    )
    await graph.ainvoke(
        {"messages": [HumanMessage("Вопрос в чате B", id="msg-b")]},
        config=run_config("chat-b"),
        context=context,
    )

    state_a = await graph.aget_state(run_config("chat-a"))
    assert [m.type for m in state_a.values["messages"]] == ["human", "ai"]
    assert state_a.values["messages"][0].content == "Вопрос в чате A"


async def test_same_message_id_is_not_duplicated(graph):
    context = AgentContext(user_id=uuid.uuid4())

    await graph.ainvoke(
        {"messages": [HumanMessage("Вопрос в чате C", id="msg-c")]},
        config=run_config("chat-c"),
        context=context,
    )

    await graph.ainvoke(
        {"messages": [HumanMessage("Вопрос в чате C, дубль", id="msg-c")]},
        config=run_config("chat-c"),
        context=context,
    )

    state = await graph.aget_state(run_config("chat-c"))
    assert state.values["messages"][0].content == "Вопрос в чате C, дубль"
    assert [message.type for message in state.values["messages"]] == [
        "human",
        "ai",
        "ai",
    ]


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(ResponseError("", 503), id="ollama_503"),
        pytest.param(httpx.ConnectError("connection refused"), id="ollama_down"),
    ],
)
async def test_provider_error_becomes_llm_unavailable(error):
    graph = build_graph(
        FailingFakeModel(messages=iter([]), error=error), InMemorySaver()
    )

    with pytest.raises(LLMUnavailableError) as exc_info:
        await graph.ainvoke(
            {"messages": [HumanMessage("Привет", id="msg-1")]},
            config=run_config("chat-1"),
            context=AgentContext(user_id=uuid.uuid4()),
        )

    assert exc_info.value.__cause__ is error
