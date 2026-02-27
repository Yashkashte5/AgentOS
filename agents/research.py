from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from tools.search import web_search
from config import GROQ_API_KEY, STRONG_MODEL

llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are a research agent. You have access to web search results.
Summarize the findings concisely and factually. Focus only on what's relevant to the task.
Do not add opinions. Output plain text, no markdown headers."""

def research_node(state: AgentState) -> dict:
    task = state["task"]

    # search the web
    search_results = web_search(task)

    response = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Task: {task}\n\nSearch results:\n{search_results}\n\nSummarize what's relevant.")
    ])

    outputs = state.get("agent_outputs", {})
    outputs["research"] = response.content

    current = state.get("current_step", 0)
    return {
        "agent_outputs": outputs,
        "current_step": current + 1,
    }