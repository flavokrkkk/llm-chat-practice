from langchain_core.tools import ToolException, tool
from langgraph.prebuilt import ToolRuntime

from app.agent.graph.state import AgentContext
from app.agent.tools.deps import ToolDeps
from app.core.services.user_service import UserService


def make_get_balance(deps: ToolDeps):
    @tool
    async def get_balance(runtime: ToolRuntime[AgentContext]):
        """Показать текущий баланс счёта клиента."""

        user_id = runtime.context.user_id

        async with deps.session_factory() as session:
            user = await UserService(session, deps.cache).get_user_by_id(user_id)

        if user is None:
            raise ToolException("Счёт клиента не найден")

        return f"Баланс счёта: {user.balance:,.2f}".replace(",", " ")

    return get_balance
