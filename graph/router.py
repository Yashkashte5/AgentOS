from graph.state import AgentState
from config import MAX_RETRIES


def route_after_supervisor(state: AgentState) -> str:
    """After supervisor sets the plan, kick off step 0."""
    plan = state.get("plan", [])
    if not plan:
        return "synthesizer"
    return plan[0]


def route_after_agent(state: AgentState) -> str:
    """After any non-code agent finishes, move to next plan step or synthesize.
    NOTE: agents already increment current_step before returning, so we read it directly.
    """
    plan = state.get("plan", [])
    current = state.get("current_step", 0)

    if current >= len(plan):
        return "synthesizer"

    return plan[current]


INFRASTRUCTURE_ERRORS = [
    "socket",
    "AF_UNIX",
    "docker",
    "server API version",
    "ConnectionRefusedError",
    "FileNotFoundError",
    "timeout",
]

def _is_infrastructure_error(error: str) -> bool:
    """Returns True if the error is Docker/infra related, not a code bug."""
    error_lower = error.lower()
    return any(keyword.lower() in error_lower for keyword in INFRASTRUCTURE_ERRORS)


def route_after_executor(state: AgentState) -> str:
    """After code execution: retry on error, or continue plan."""
    error = state.get("execution_error", "")
    retries = state.get("retry_count", 0)

    if error and retries < MAX_RETRIES and not _is_infrastructure_error(error):
        return "self_heal"

    # router is solely responsible for advancing past code/executor
    plan = state.get("plan", [])
    current = state.get("current_step", 0)
    next_step = current + 1

    if next_step >= len(plan):
        return "synthesizer"

    return plan[next_step]


def route_after_self_heal(state: AgentState) -> str:
    """Self-heal always sends back to executor to retry."""
    return "executor"