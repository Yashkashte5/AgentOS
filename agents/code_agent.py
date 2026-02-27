from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from config import GROQ_API_KEY, STRONG_MODEL

llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are an expert Python programmer.
Write clean, complete, runnable Python code for the given task.
Only use these available packages: python standard library, requests.
Do NOT use bs4, beautifulsoup, pandas, numpy, matplotlib or any other third-party packages.
If web scraping is needed, use requests and parse the response manually with string methods or regex.
If the task context contains API data, use that data directly rather than making new API calls.
Return ONLY the raw code — no markdown fences, no explanations, no comments unless necessary."""

def code_node(state: AgentState) -> dict:
    task = state["task"]
    research = state.get("agent_outputs", {}).get("research", "")

    context = f"Task: {task}"
    if research:
        context += f"\n\nResearch context:\n{research}"

    response = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=context)
    ])

    return {
        "code": response.content.strip(),
        "language": "python",
        "execution_error": "",
        "retry_count": 0,
    }