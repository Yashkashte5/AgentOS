from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    
    task: str
    plan: list[str]
    current_step: int
    next: str

    agent_outputs: dict
    
    code: str
    language: str
    execution_result: str
    execution_error: str
    retry_count: int


    final_output: str

    messages: Annotated[list, add_messages]