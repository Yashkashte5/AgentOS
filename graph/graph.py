from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.router import (
    route_after_supervisor,
    route_after_agent,
    route_after_executor,
    route_after_self_heal,
)
from agents.supervisor   import supervisor_node
from agents.research     import research_node
from agents.code_agent   import code_node
from agents.self_heal    import self_heal_node
from agents.file_agent   import file_node
from agents.api_agent    import api_node
from agents.synthesizer  import synthesizer_node
from tools.executor      import executor_node


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    
    g.add_node("supervisor",  supervisor_node)
    g.add_node("research",    research_node)
    g.add_node("code",        code_node)
    g.add_node("executor",    executor_node)
    g.add_node("self_heal",   self_heal_node)
    g.add_node("file",        file_node)
    g.add_node("api",         api_node)
    g.add_node("synthesizer", synthesizer_node)

    
    g.set_entry_point("supervisor")

    
    g.add_conditional_edges("supervisor", route_after_supervisor, {
        "research":    "research",
        "code":        "code",
        "file":        "file",
        "api":         "api",
        "synthesizer": "synthesizer",
    })

    
    for node in ["research", "file", "api"]:
        g.add_conditional_edges(node, route_after_agent, {
            "research":    "research",
            "code":        "code",
            "file":        "file",
            "api":         "api",
            "synthesizer": "synthesizer",
        })

    
    g.add_edge("code", "executor")

    
    g.add_conditional_edges("executor", route_after_executor, {
        "self_heal":   "self_heal",
        "research":    "research",
        "code":        "code",
        "file":        "file",
        "api":         "api",
        "synthesizer": "synthesizer",
    })

    
    g.add_conditional_edges("self_heal", route_after_self_heal, {
        "executor": "executor",
    })


    g.add_edge("synthesizer", END)

    return g.compile()


graph = build_graph()