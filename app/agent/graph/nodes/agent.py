from langchain_core.language_models import BaseChatModel

from app.agent.graph.state import AgentState
from app.agent.prompts.system import get_system_prompt


def make_agent_node(llm: BaseChatModel):
    async def agent(state: AgentState) -> dict:
        res = await llm.ainvoke(get_system_prompt(), state=state)

        return {"messages": [res.content]}

    return agent
