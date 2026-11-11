import asyncio

from langchain_core.messages import HumanMessage

from app.agent.graph.pipeline import build_graph
from app.agent.llm import create_chat_model
from app.infrastructure.config.config import settings


async def main():
    llm = create_chat_model(settings.llm)

    graph = build_graph(llm)

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Привет! обменяй доллары")]}
    )

    for message in result["messages"]:
        print(f"[{message.type}] {message.content}")


if __name__ == "__main__":
    asyncio.run(main())
