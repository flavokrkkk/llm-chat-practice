import logging

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.agent.graph.state import AgentState
from app.agent.guards import looks_like_text_tool_call
from app.agent.llm import LLM_PROVIDER_ERRORS
from app.agent.prompts.system import FALLBACK_REPLY, get_system_prompt
from app.infrastructure.errors.exceptions import LLMUnavailableError

logger = logging.getLogger(__name__)


def make_agent_node(
    llm: Runnable[LanguageModelInput, AIMessage], tool_names: frozenset[str]
):

    async def agent(state: AgentState) -> dict:
        messages = [SystemMessage(get_system_prompt()), *state["messages"]]

        try:
            response = await llm.ainvoke(messages)
        except LLM_PROVIDER_ERRORS as exc:
            logger.warning("LLM provider error: %r", exc, exc_info=True)
            raise LLMUnavailableError("LLM unavailable") from exc

        if not response.tool_calls and looks_like_text_tool_call(
            response.text, tool_names
        ):
            logger.warning("Model wrote tool call as text: %s", response.text[:200])
            response = AIMessage(
                content=FALLBACK_REPLY,
                usage_metadata=response.usage_metadata,
            )

        return {"messages": [response]}

    return agent
