import os
from typing import Literal
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from graph.state import AgentState
from config import GROQ_API_KEY, LIGHT_MODEL


class FileOperation(BaseModel):
    operation: Literal["read", "write"] = Field(description="read or write")
    path: str = Field(description="filename only, no absolute path")


llm = ChatGroq(model=LIGHT_MODEL, api_key=GROQ_API_KEY, temperature=0)
structured_llm = llm.with_structured_output(FileOperation)

SYSTEM = """You are a file operations agent.
Given a task, decide whether to read or write a file and which filename to use.
Use simple filenames only, no absolute paths.
Do NOT generate content — content is always provided to you separately."""


def _strip_fences(code: str) -> str:
    """Remove markdown code fences if LLM wrapped the code."""
    lines = code.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def file_node(state: AgentState) -> dict:
    task             = state["task"]
    executed_code    = state.get("code", "")
    execution_result = state.get("execution_result", "")

    BASE = os.path.dirname(os.path.abspath(__file__ + "/../"))
    OUTPUTS_DIR = os.path.join(BASE, "outputs")
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    result = ""
    try:
        op: FileOperation = structured_llm.invoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Task: {task}")
        ])

        if op.operation == "write":
            path = os.path.join(OUTPUTS_DIR, op.path)

            if executed_code:
                content = _strip_fences(executed_code)
                if execution_result:
                    comment_lines = execution_result.replace("\n", "\n# ")
                    content += f"\n\n# Execution output:\n# {comment_lines}"
            else:
                content = f"# No code was executed for task: {task}"

            with open(path, "w") as f:
                f.write(content)
            result = f"Written to outputs/{op.path}"

        elif op.operation == "read":
            path = os.path.join(BASE, op.path)
            if not os.path.exists(path):
                path = os.path.join(OUTPUTS_DIR, op.path)
            if os.path.exists(path):
                with open(path) as f:
                    result = f.read()
            else:
                result = f"File not found: {op.path}"

    except Exception as e:
        result = f"File operation failed: {str(e)}"

    outputs = state.get("agent_outputs", {})
    outputs["file"] = result
    current = state.get("current_step", 0)

    return {
        "agent_outputs": outputs,
        "current_step": current + 1,
    }