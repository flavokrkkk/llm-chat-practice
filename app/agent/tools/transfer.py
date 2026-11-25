from decimal import Decimal

from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime
from pydantic import EmailStr, Field

from app.agent.graph.state import AgentContext
from app.agent.tools.deps import ToolDeps


def make_create_transfer(deps: ToolDeps) -> BaseTool:
    @tool
    async def create_transfer(
        runtime: ToolRuntime[AgentContext],
        email: EmailStr,
        amount: Decimal = Field(..., gt=0, decimal_places=2),
    ):
        pass

    return create_transfer
