from langchain_core.tools import BaseTool

from app.agent.tools.balance import make_get_balance
from app.agent.tools.deps import ToolDeps


def make_tools(deps: ToolDeps) -> list[BaseTool]:
    return [make_get_balance(deps)]
