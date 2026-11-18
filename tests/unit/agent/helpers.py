from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from tests.unit.agent.fakes import RecordingFakeModel


def run_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def model_calling_tool(tool_name: str, final_answer: str) -> RecordingFakeModel:
    """Модель, которая сначала вызывает инструмент, потом отвечает текстом."""
    return RecordingFakeModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[{"name": tool_name, "args": {}, "id": "call_1"}],
                ),
                AIMessage(final_answer),
            ]
        )
    )
