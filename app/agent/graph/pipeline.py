from langgraph.graph import END, START, StateGraph

from app.agent.graph.nodes.agent import make_agent_node


async def build_graph(llm) -> StateGraph:
    workflow = StateGraph(llm)

    workflow.add_edge("Start", START)

    workflow.add_node(make_agent_node(llm))

    workflow.add_edge("Final", END)

    app: StateGraph = workflow.compile()  # type: ignore

    return app
