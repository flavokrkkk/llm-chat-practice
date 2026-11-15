from langchain_core.messages import AIMessage
from langgraph.graph import END

from app.agent.graph.state import AgentState
from app.utils.enums import Node


def route_after_agent(state: AgentState) -> str:
    """Есть вызовы инструментов — выполняем их, иначе ответ готов."""
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return Node.TOOLS

    return END
