from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage

from app.agent.graph.state import AgentState
from app.agent.prompts.system import get_system_prompt


def make_agent_node(llm: BaseChatModel):
    async def agent(state: AgentState) -> dict:
        messages = [SystemMessage(get_system_prompt()), *state["messages"]]
        response = await llm.ainvoke(messages)

        return {"messages": [response]}

    return agent
