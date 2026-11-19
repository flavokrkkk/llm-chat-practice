from typing import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agent.graph.nodes.agent import make_agent_node
from app.agent.graph.nodes.tools import make_tools_node
from app.agent.graph.routing import route_after_agent
from app.agent.graph.state import AgentContext, AgentGraph, AgentState
from app.utils.enums import Node


def build_graph(
    llm: BaseChatModel,
    tools: Sequence[BaseTool],
    checkpointer: BaseCheckpointSaver | None = None,
) -> AgentGraph:
    builder = StateGraph(AgentState, context_schema=AgentContext)
    tool_names = frozenset(t.name for t in tools)

    builder.add_node(Node.AGENT, make_agent_node(llm.bind_tools(tools), tool_names))
    builder.add_node(Node.TOOLS, make_tools_node(tools))

    builder.add_edge(START, Node.AGENT)
    builder.add_conditional_edges(Node.AGENT, route_after_agent, [Node.TOOLS, END])
    builder.add_edge(Node.TOOLS, Node.AGENT)

    compiled: AgentGraph = builder.compile(checkpointer=checkpointer)

    return compiled
