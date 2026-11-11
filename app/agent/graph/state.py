from dataclasses import dataclass
from typing import Annotated, TypedDict
from uuid import UUID

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph


@dataclass
class AgentContext:
    user_id: UUID


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


AgentGraph = CompiledStateGraph[AgentState, AgentContext, AgentState, AgentState]
