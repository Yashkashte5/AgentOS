from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from config import GROQ_API_KEY, STRONG_MODEL

llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are a debugging expert.
You will be given broken Python code and its error message.
Fix the code so it runs correctly.
Return ONLY the corrected raw code — no markdown fences, no explanations."""

def self_heal_node(state: AgentState) -> dict:
    code = state.get("code", "")
    error = state.get("execution_error", "")
    retry_count = state.get("retry_count", 0)

    response = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Broken code:\n{code}\n\nError:\n{error}\n\nFix it.")
    ])

    return {
        "code": response.content.strip(),
        "execution_error": "",          # reset so executor runs fresh
        "retry_count": retry_count + 1,
    }