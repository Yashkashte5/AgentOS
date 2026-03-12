from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from config import GROQ_API_KEY, STRONG_MODEL


_task_store = None

def set_task_store(store: dict):
    """Called from main.py to inject the shared tasks dict."""
    global _task_store
    _task_store = store


llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are the final synthesizer agent. You receive outputs from all other agents and produce the final response shown to the user.

YOUR JOB: Write a clear, complete, and accurate final response based strictly on what the agents actually did.

CONTENT RULES:
- Only report what actually happened — never invent results, fabricate outputs, or assume success
- If code was executed, lead with the actual execution output and what it demonstrates
- If research was done, present the findings in a clean, readable way
- If an API call returned data, lead directly with the data and what it means
- If a file was saved, confirm the filename and what was written to it
- If something failed, state clearly what failed and why — do not hide errors
- If code was written but produced no output, say so honestly

FORMATTING RULES:
- Write in clear prose — not a list of "Agent X did Y" summaries
- Do not narrate the pipeline ("The research agent searched...", "The code agent wrote...")
- Do not use markdown headers (##, ###)
- Use inline code formatting for variable names, filenames, function names
- Keep it concise — say everything once, say it well

TONE:
- Direct and factual — not enthusiastic, not apologetic
- If the task was completed successfully, confirm it plainly
- If the task failed or was only partially completed, be honest about it"""


def synthesizer_node(state: AgentState) -> dict:
    task    = state["task"]
    outputs = state.get("agent_outputs", {})
    code    = state.get("code", "")
    result  = state.get("execution_result", "")
    error   = state.get("execution_error", "")
    retries = state.get("retry_count", 0)
    task_id = state.get("task_id", "")

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
    messages = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=context),
    ]

    full_text = ""


    if _task_store is not None and task_id and task_id in _task_store:
        token_buffer = []
        _task_store[task_id]["synth_tokens"] = token_buffer

        try:
            for chunk in llm.stream(messages):
                token = chunk.content
                if token:
                    full_text += token
                    token_buffer.append(token)
        except Exception:
            full_text = llm.invoke(messages).content

        token_buffer.append("__DONE__")

    else:
        full_text = llm.invoke(messages).content

    return {"final_output": full_text}