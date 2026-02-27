import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from graph.state import AgentState
from config import GROQ_API_KEY, LIGHT_MODEL


class APICall(BaseModel):
    url: str = Field(description="Full URL including path")
    method: str = Field(description="HTTP method: GET or POST")
    params: dict = Field(default={}, description="Query parameters")
    headers: dict = Field(default={}, description="Request headers")


llm = ChatGroq(model=LIGHT_MODEL, api_key=GROQ_API_KEY, temperature=0)
structured_llm = llm.with_structured_output(APICall)

SYSTEM = """You are an API agent. Given a task, determine the correct free public API call to make.
Use only APIs that require no authentication.
Always construct a complete, valid URL with all necessary parameters."""

def api_node(state: AgentState) -> dict:
    task = state["task"]

    result = ""
    try:
        api_call: APICall = structured_llm.invoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Task: {task}")
        ])

        response = requests.request(
            api_call.method,
            api_call.url,
            params=api_call.params,
            headers=api_call.headers,
            timeout=10
        )
        result = response.text[:2000]

    except Exception as e:
        result = f"API call failed: {str(e)}"

    outputs = state.get("agent_outputs", {})
    outputs["api"] = result
    current = state.get("current_step", 0)

    return {
        "agent_outputs": outputs,
        "current_step": current + 1,
    }