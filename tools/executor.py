import subprocess
import sys
import tempfile
import os
from graph.state import AgentState
from config import EXECUTION_TIMEOUT


def executor_node(state: AgentState) -> dict:
    """Run code in a subprocess with timeout. Falls back gracefully if execution fails."""
    code     = state.get("code", "")
    language = state.get("language", "python")

    if not code:
        return {"execution_error": "No code to execute."}


    code = _clean_code(code)

    try:

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py" if language == "python" else ".sh",
            delete=False
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            cmd = [sys.executable, tmp_path] if language == "python" else ["bash", tmp_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT,
            )
        finally:
            os.unlink(tmp_path)

        if result.returncode == 0:
            stdout = result.stdout.strip()

            if not stdout:
                return {
                    "execution_result": "",
                    "execution_error": "Code ran successfully but produced no output. Check logic.",
                }
            outputs = state.get("agent_outputs", {})
            outputs["code_result"] = stdout
            return {
                "execution_result": stdout,
                "execution_error": "",
                "agent_outputs": outputs,
            }
        else:
            return {
                "execution_result": "",
                "execution_error": result.stderr.strip(),
            }

    except subprocess.TimeoutExpired:
        return {
            "execution_result": "",
            "execution_error": f"Execution timed out after {EXECUTION_TIMEOUT}s",
        }
    except Exception as e:
        return {
            "execution_result": "",
            "execution_error": str(e),
        }


def _clean_code(code: str) -> str:
    """Strip markdown code fences that the LLM sometimes adds."""
    lines = code.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)