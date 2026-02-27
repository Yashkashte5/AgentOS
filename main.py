import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from graph.graph import graph

app = FastAPI(title="AgentOS", version="1.0.0")

# in-memory task store (swap for Redis in production)
tasks: dict = {}


# ── request / response models ──────────────────────────────────────────────

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    task_id: str
    status: str          # "pending" | "running" | "done" | "error"
    result: str | None = None
    trace: list  | None = None


# ── background runner ──────────────────────────────────────────────────────

def run_graph(task_id: str, task: str):
    tasks[task_id]["status"] = "running"
    try:
        initial_state = {
            "task": task,
            "plan": [],
            "current_step": 0,
            "next": "",
            "agent_outputs": {},
            "code": "",
            "language": "python",
            "execution_result": "",
            "execution_error": "",
            "retry_count": 0,
            "final_output": "",
            "messages": [],
        }

        final_state = graph.invoke(initial_state)

        tasks[task_id]["status"] = "done"
        tasks[task_id]["result"] = final_state.get("final_output", "No output generated.")
        tasks[task_id]["trace"]  = _extract_trace(final_state)

    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["result"] = str(e)


def _extract_trace(state: dict) -> list:
    """Pull a human-readable trace from final state."""
    trace = []
    outputs = state.get("agent_outputs", {})
    for agent, output in outputs.items():
        trace.append({"agent": agent, "output": str(output)[:500]})
    if state.get("code"):
        trace.append({"agent": "code_writer", "output": state["code"][:500]})
    if state.get("execution_result"):
        trace.append({"agent": "executor", "output": state["execution_result"][:500]})
    if state.get("retry_count", 0) > 0:
        trace.append({"agent": "self_heal", "output": f"Healed {state['retry_count']} time(s)"})
    return trace


# ── routes ─────────────────────────────────────────────────────────────────

@app.post("/task", response_model=TaskResponse, status_code=202)
async def submit_task(body: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None, "trace": None}
    background_tasks.add_task(run_graph, task_id, body.task)
    return TaskResponse(task_id=task_id, status="pending")


@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    t = tasks[task_id]
    return TaskResponse(task_id=task_id, **t)


@app.get("/task/{task_id}/trace")
async def get_trace(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "trace": tasks[task_id].get("trace", [])}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AgentOS"}