import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.graph.pipeline import build_graph
from app.agent.graph.state import AgentGraph
from tests.unit.agent.fakes import RecordingFakeModel


@pytest.fixture
def fake_llm() -> RecordingFakeModel:
    return RecordingFakeModel(
        messages=iter([AIMessage("Первый ответ"), AIMessage("Второй ответ")])
    )


@pytest.fixture
def graph(fake_llm) -> AgentGraph:
    return build_graph(fake_llm, InMemorySaver())
