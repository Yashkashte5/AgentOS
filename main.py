import uuid
import json
import asyncio
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.graph import graph
from agents.synthesizer import set_task_store




app = FastAPI(title="AgentOS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


tasks: dict = {}


set_task_store(tasks)




DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id          TEXT PRIMARY KEY,
                task        TEXT NOT NULL,
                result      TEXT,
                plan        TEXT,
                created_at  TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def save_to_history(task_id: str, task: str, result: str, plan: list):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO task_history (id, task, result, plan, created_at) VALUES (?, ?, ?, ?, ?)",
            (task_id, task, result, json.dumps(plan), datetime.utcnow().isoformat())
        )
        conn.commit()

def load_history(limit: int = 20) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, task, result, plan, created_at FROM task_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]



class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None
    trace:  list | None = None



async def stream_graph_task(task_id: str, task: str):
    """Run the graph with streaming, pushing SSE chunks into tasks[task_id]['chunks']."""
    tasks[task_id]["status"] = "running"
    chunks = tasks[task_id]["chunks"]

    try:
        initial_state = {
            "task": task,
            "task_id": task_id,
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

        loop = asyncio.get_event_loop()
        plan = []
        result = ""

        def run_graph_sync():
            nonlocal plan, result
            final_state = {}
            for chunk in graph.stream(initial_state, stream_mode="updates"):
                node_name = list(chunk.keys())[0]
                node_data = chunk[node_name]

              
                if node_name == "supervisor" and "plan" in node_data:
                    plan = node_data.get("plan", [])


                if node_name == "synthesizer":
                    result = node_data.get("final_output", "")

                chunks.append({"type": "chunk", "node": node_name, "data": chunk})
                final_state = node_data

            return final_state

        await loop.run_in_executor(None, run_graph_sync)

        chunks.append({"type": "done", "result": result, "plan": plan})
        tasks[task_id]["status"] = "done"
        tasks[task_id]["result"] = result


        save_to_history(task_id, task, result, plan)

    except Exception as e:
        chunks.append({"type": "error", "message": str(e)})
        tasks[task_id]["status"] = "error"
        tasks[task_id]["result"] = str(e)



@app.get("/task/{task_id}/stream")
async def stream_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        sent = 0
        while True:
            chunks = tasks.get(task_id, {}).get("chunks", [])
            while sent < len(chunks):
                chunk = chunks[sent]
                yield f"data: {json.dumps(chunk)}\n\n"
                sent += 1
                if chunk["type"] in ("done", "error"):
                    return
            await asyncio.sleep(0.15)

    return StreamingResponse(event_generator(), media_type="text/event-stream")




@app.get("/task/{task_id}/synthesizer-stream")
async def stream_synthesizer_tokens(task_id: str):
    """
    Streams the synthesizer's LLM response token by token.
    synthesizer_node pushes tokens into tasks[task_id]['synth_tokens'].
    '__DONE__' sentinel signals end of stream.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def token_generator():
        waited = 0
        while "synth_tokens" not in tasks.get(task_id, {}):
            await asyncio.sleep(0.1)
            waited += 1
            if waited > 900:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Synthesizer stream timeout'})}\n\n"
                return

        sent = 0
        while True:
            tokens = tasks[task_id].get("synth_tokens", [])
            while sent < len(tokens):
                token = tokens[sent]
                sent += 1
                if token == "__DONE__":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
            await asyncio.sleep(0.04)

    return StreamingResponse(token_generator(), media_type="text/event-stream")



@app.post("/task", response_model=TaskResponse, status_code=202)
async def submit_task(body: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "result": None,
        "trace": None,
        "chunks": [],
    }
    background_tasks.add_task(stream_graph_task, task_id, body.task)
    return TaskResponse(task_id=task_id, status="pending")


@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    t = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=t["status"],
        result=t.get("result"),
        trace=t.get("trace"),
    )


@app.get("/history")
async def get_history(limit: int = 20):
    """Load persisted task history from SQLite."""
    return {"history": load_history(limit)}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AgentOS"}