from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from config import GROQ_API_KEY, STRONG_MODEL

llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are a synthesizer. Your ONLY job is to summarize what the other agents actually did.

Critical rules:
- NEVER write code yourself
- NEVER save files yourself  
- NEVER pretend something happened if it is not in the agent outputs
- If code was not executed, say so clearly — do not fabricate results
- If a file was not saved, say so clearly — do not pretend it was
- Only report what actually happened based on the agent outputs provided to you
- Be concise and factual"""

def synthesizer_node(state: AgentState) -> dict:
    task    = state["task"]
    outputs = state.get("agent_outputs", {})
    code    = state.get("code", "")
    result  = state.get("execution_result", "")
    error   = state.get("execution_error", "")
    retries = state.get("retry_count", 0)

    parts = [f"Original task: {task}\n"]

    if outputs.get("research"):
        parts.append(f"Research findings:\n{outputs['research']}\n")

    if code:
        parts.append(f"Code that was written and executed:\n{code}\n")
    else:
        parts.append("No code was written or executed.\n")

    if result:
        parts.append(f"Actual execution output:\n{result}\n")
    elif code:
        parts.append("Code was written but execution produced no output or failed.\n")

    if error:
        parts.append(f"Execution failed after {retries} fix attempt(s). Last error:\n{error}\n")

    if outputs.get("file"):
        parts.append(f"File operations:\n{outputs['file']}\n")

    if outputs.get("api"):
        parts.append(f"API response:\n{outputs['api']}\n")

    context = "\n".join(parts)

    response = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=context)
    ])

    return {"final_output": response.content}