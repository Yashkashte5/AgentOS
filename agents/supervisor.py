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

SYSTEM = """You are a task planning supervisor for a multi-agent AI system.
Your ONLY job is to decide the minimum set of agents needed to complete the task correctly.
Return an ordered list. Every agent you add has a cost — never add one unless it is strictly required.

AGENTS AND WHAT THEY DO:
- research : Searches the web and summarizes findings. Use for information, explanations, comparisons, "what is X", "how does X work", recent news, documentation lookups. Can include illustrative code snippets in its output.
- code     : Writes Python code AND executes it. Use only when the task requires actual computation, data processing, a working implementation, algorithm execution, or generating output that must be run.
- api      : Makes a live HTTP call to a free public API. Use only for real-time data: current prices, live weather, exchange rates, sports scores, public datasets.
- file     : Saves content to disk. Use only when the user explicitly asks to save, export, or persist something to a file.

STRICT ORDERING RULES (never break these):
- research always comes before code or api if both are in the plan
- code always comes before file if both are in the plan
- file is always last

DECISION GUIDE — think through each task type:
"What is X / explain X / tell me about X / how does X work"  → [research] only
"Difference between X and Y / compare X and Y"               → [research] only
"Implement X / build X / write a program that does X"        → [code] only
"Research X then implement it"                               → [research, code]
"Research X, implement it, and save to a file"               → [research, code, file]
"Current price / live data / today's weather"                → [api] only
"Implement X and save it"                                    → [code, file]
"Read/write a file"                                          → [file] only

NEVER add code just because the topic involves programming — if the user wants an explanation, research is enough.
NEVER add file unless the user explicitly says save, export, write to file, or persist.
NEVER add api for historical or conceptual questions — only for live real-time data.
NEVER add research if the task is purely computational and needs no background knowledge."""


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