from app.agent.graph.pipeline import build_graph
from app.agent.llm import create_chat_model
from app.infrastructure.config.config import settings


async def create_model_agent():
    chat = create_chat_model(settings.llm)

    res = await build_graph(chat)

    return res
