from typing import Annotated, Sequence
from uuid import UUID

from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime
from pydantic import Field

from app.agent.graph.state import AgentContext
from app.agent.tools.deps import ToolDeps
from app.core.schemas.transfer import TransferSchema
from app.core.services.transfer_service import TransferService


def format_history(transfers: Sequence[TransferSchema], user_id: UUID, currency: str):
    if not transfers:
        return "У клиента пока нет переводов."

    lines = [f"Последние переводы ({len(transfers)}):"]

    for t in transfers:
        direction = "исходящий" if t.from_user_id == user_id else "входящий"

        when = t.created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(f"- {when}, {direction}, {t.amount} {currency}")

    return "\n".join(lines)


def make_get_history(deps: ToolDeps) -> BaseTool:

    @tool
    async def get_history(
        runtime: ToolRuntime[AgentContext],
        limit: Annotated[int, Field(ge=1, le=20)] = 5,
    ) -> str:
        """Показать последние переводы клиента: входящие и исходящие.

        limit — сколько последних переводов показать (1–20).
        Если клиент не назвал количество, не спрашивайте, а вызовите
        инструмент без этого параметра — будет показано 5 последних.
        """
        user_id = runtime.context.user_id

        async with deps.session_factory() as session:
            transfer_history = await TransferService(
                session, demo_delay=deps.transfer_demo_delay
            ).get_transfers_history(user_id=user_id, limit=limit)

            return format_history(
                transfers=transfer_history.items,
                user_id=user_id,
                currency=deps.currency,
            )

    return get_history
