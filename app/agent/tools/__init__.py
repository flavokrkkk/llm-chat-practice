from langchain_core.tools import BaseTool

from app.agent.tools.balance import make_get_balance
from app.agent.tools.deps import ToolDeps
from app.agent.tools.history import make_get_history
from app.agent.tools.recipient import make_find_recipient


def make_tools(deps: ToolDeps) -> list[BaseTool]:
    return [make_get_balance(deps), make_get_history(deps), make_find_recipient(deps)]
