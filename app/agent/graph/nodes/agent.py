from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage

from app.agent.graph.state import AgentState
from app.agent.llm import LLM_PROVIDER_ERRORS
from app.agent.prompts.system import get_system_prompt
from app.infrastructure.errors.exceptions import LLMUnavailableError


def make_agent_node(llm: BaseChatModel):

    async def agent(state: AgentState) -> dict:
        messages = [SystemMessage(get_system_prompt()), *state["messages"]]

        try:
            response = await llm.ainvoke(messages)
        except LLM_PROVIDER_ERRORS as exc:
            raise LLMUnavailableError("LLM unavailable") from exc

        return {"messages": [response]}

    return agent
