from langchain_core.tools import BaseTool

from app.agent.tools.balance import make_get_balance
from app.agent.tools.deps import ToolDeps
from app.agent.tools.history import make_get_history


def make_tools(deps: ToolDeps) -> list[BaseTool]:
    return [make_get_balance(deps), make_get_history(deps)]
