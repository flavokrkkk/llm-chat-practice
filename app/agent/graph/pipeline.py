from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agent.graph.nodes.agent import make_agent_node
from app.agent.graph.state import AgentContext, AgentGraph, AgentState
from app.utils.enums import Node


def build_graph(
    llm: BaseChatModel, checkpointer: BaseCheckpointSaver | None = None
) -> AgentGraph:
    builder = StateGraph(AgentState, context_schema=AgentContext)

    builder.add_node(Node.AGENT, make_agent_node(llm))

    builder.add_edge(START, Node.AGENT)
    builder.add_edge(Node.AGENT, END)

    compiled: AgentGraph = builder.compile(checkpointer=checkpointer)

    return compiled
