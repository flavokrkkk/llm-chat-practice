import logging

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.agent.graph.state import AgentState
from app.agent.llm import LLM_PROVIDER_ERRORS
from app.agent.prompts.system import get_system_prompt
from app.infrastructure.errors.exceptions import LLMUnavailableError

logger = logging.getLogger(__name__)


def make_agent_node(llm: Runnable[LanguageModelInput, AIMessage]):

    async def agent(state: AgentState) -> dict:
        messages = [SystemMessage(get_system_prompt()), *state["messages"]]

        try:
            response = await llm.ainvoke(messages)
        except LLM_PROVIDER_ERRORS as exc:
            logger.warning("LLM provider error: %r", exc, exc_info=True)
            raise LLMUnavailableError("LLM unavailable") from exc

        return {"messages": [response]}

    return agent
