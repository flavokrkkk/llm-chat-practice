from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.graph.nodes.agent import make_agent_node
from app.agent.graph.state import AgentState
from app.utils.enums import Node


def build_graph(
    llm: BaseChatModel, checkpointer: BaseCheckpointSaver | None = None
) -> CompiledStateGraph:
    builder = StateGraph(AgentState)

    builder.add_node(Node.AGENT, make_agent_node(llm))

    builder.add_edge(START, Node.AGENT)
    builder.add_edge(Node.AGENT, END)

    compiled: CompiledStateGraph = builder.compile(checkpointer=checkpointer)

    return compiled
