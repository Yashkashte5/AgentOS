from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from tools.search import web_search
from config import GROQ_API_KEY, STRONG_MODEL

llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are a research agent with access to live web search results.
Your job is to produce a thorough, accurate, well-structured response to the task using the search results provided.

RULES:
- Ground your answer in the search results — do not hallucinate facts
- If search results are poor or irrelevant, fall back to your own knowledge and say so clearly
- Write in clear, readable prose — no excessive bullet points, no padding
- Do not use markdown headers (##, ###) — use plain section labels if needed
- Be comprehensive but not repetitive — cover the topic fully in as few words as possible
- If the task is about a concept or technology, include:
  • A clear definition and explanation
  • Key characteristics or properties
  • Real-world use cases or examples
  • Trade-offs, limitations, or important caveats
  • A short illustrative code snippet if it would help understanding (wrap in ``` fences)
- If the task is a comparison ("X vs Y"), cover both sides fairly and end with a clear summary
- If the task asks for recent news or current events, prioritize the most recent results
- Never add opinions or recommendations unless explicitly asked
- Output only the response — no preamble like "Based on the search results..." """

def research_node(state: AgentState) -> dict:
    task = state["task"]

    search_results = web_search(task)

    # short-circuit if search failed or returned nothing useful
    if not search_results or search_results.startswith("No results") or search_results.startswith("Search failed"):
        summary = f"Web search returned no results for: {task}. Proceeding with model knowledge only."
    else:
        response = llm.invoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Task: {task}\n\nSearch results:\n{search_results}\n\nSummarize what's relevant.")
        ])
        summary = response.content

    outputs = state.get("agent_outputs", {})
    outputs["research"] = summary

    current = state.get("current_step", 0)
    return {
        "agent_outputs": outputs,
        "current_step": current + 1,
    }