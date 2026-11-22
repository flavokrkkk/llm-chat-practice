from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime
from pydantic import EmailStr

from app.agent.graph.state import AgentContext
from app.agent.tools.deps import ToolDeps
from app.core.services.user_service import UserService


def mask_name(full_name: str) -> str:
    """«Иван Петров» → «Иван П.»"""
    parts = full_name.split()
    if not parts:
        return "клиент банка"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


def make_find_recipient(deps: ToolDeps) -> BaseTool:

    @tool
    async def find_recipient(
        runtime: ToolRuntime[AgentContext], email: EmailStr
    ) -> str:
        """Найти клиента банка по точному email, чтобы подготовить перевод.

        email — точный адрес получателя, который назвал клиент.
        """

        async with deps.session_factory() as session:
            user = await UserService(session, deps.cache).find_user_by_email(email)

            if user is None or not user.is_active:
                return f"Клиент с email {email} не найден"

            if user.id == runtime.context.user_id:
                return "Это ваш собственный счёт"

        return f"Получатель найден: {mask_name(user.full_name)}"

    return find_recipient
