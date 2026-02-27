from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import List, Literal
from graph.state import AgentState
from config import GROQ_API_KEY, STRONG_MODEL


class SupervisorPlan(BaseModel):
    plan: List[Literal["research", "code", "file", "api"]] = Field(
        description="Ordered list of agents to run. Only include what is strictly necessary."
    )
    reasoning: str = Field(description="One line explanation of the plan")


llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)
structured_llm = llm.with_structured_output(SupervisorPlan)

SYSTEM = """You are a task planning supervisor for a multi-agent system.
Analyze the task carefully and return a plan — an ordered list of agents to run.

Agent responsibilities:
- research : searches the web for information, articles, documentation
- code     : writes AND executes Python code — use whenever any computation, implementation, or scripting is needed
- api      : fetches live real-time data from external services (prices, weather, scores)
- file     : reads or writes files to disk — use whenever output must be persisted

Critical dependencies you must always respect:
- If the task requires saving code or results to a file, you MUST include "code" before "file"
- If the task requires implementing something, you MUST include "code"
- If the task asks about an algorithm and wants an implementation, include both "research" and "code"
- "research" always comes before "code" or "api" when included
- "file" always comes last
- For well-known live data (crypto prices, weather, currency) use "api" directly
- For obscure APIs or unknown endpoints, use "research" before "api"

Think step by step about what the task actually requires before deciding."""


def supervisor_node(state: AgentState) -> dict:
    task = state["task"]

    plan_obj: SupervisorPlan = structured_llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Task: {task}")
    ])

    plan = plan_obj.plan

    return {
        "plan": plan,
        "current_step": 0,
        "next": plan[0] if plan else "synthesizer",
        "agent_outputs": {},
        "code": "",
        "language": "python",
        "execution_result": "",
        "execution_error": "",
        "retry_count": 0,
        "final_output": "",
    }