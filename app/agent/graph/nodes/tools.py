from typing import Sequence

from langchain_core.tools import BaseTool, ToolException
from langgraph.prebuilt import ToolNode


def make_tools_node(tools: Sequence[BaseTool]) -> ToolNode:
    return ToolNode(tools, handle_tool_errors=(ToolException,))
