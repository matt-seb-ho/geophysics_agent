"""
FastAPI backend for the GEOS Agent — Next.js interface.

Wraps GeosAgent with streaming SSE endpoints.
Run with: uvicorn frontend.api_server:app --reload --port 8000
"""

import asyncio
import json
import os
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

# Add project src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.user_io import UserInputRequired
from geos_agent.tools.utils import build_default_tools

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="GEOS Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_executor = ThreadPoolExecutor(max_workers=4)
_sessions: Dict[str, Dict[str, Any]] = {}

AVAILABLE_MODELS = [
    "moonshotai/kimi-k2.5",
    "z-ai/glm-5",
    "anthropic/claude-sonnet-4.6",
    "openai/gpt-5.2",
    "google/gemini-3.1-pro-preview",
    "openai/gpt-5.3-codex",
    "deepseek/deepseek-v3.2",
    "openai/gpt-5-mini",
    "anthropic/claude-haiku-4.5",
    "qwen/qwen3-coder-next",
    "google/gemini-3-flash-preview",
    "google/gemini-3.1-flash-lite-preview",
]

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class SessionConfig(BaseModel):
    model: str = "moonshotai/kimi-k2.5"
    provider: Optional[str] = None
    max_steps: int = 100
    workspace_path: Optional[str] = None
    enable_logging: bool = False
    log_dir: Optional[str] = None
    enable_context_projection: bool = True


class MessageRequest(BaseModel):
    message: str


class WorkspaceUpdateRequest(BaseModel):
    workspace_path: str


# ---------------------------------------------------------------------------
# Agent helpers
# ---------------------------------------------------------------------------


def _create_agent(session: Dict[str, Any], stream_callback) -> GeosAgent:
    workspace_root = Path(session["workspace"]).resolve()
    cfg = session["config"]

    agent_config = AgentConfig(
        model=cfg.model,
        provider=cfg.provider or None,
        max_steps=cfg.max_steps,
        mode="interactive",
        enable_context_projection=cfg.enable_context_projection,
    )

    tools = build_default_tools(workspace_root)
    agent = GeosAgent(
        workspace_root=workspace_root,
        tools=tools,
        config=agent_config,
        stream_callback=stream_callback,
    )
    for t in agent.tools:
        if hasattr(t, "blocking"):
            t.blocking = False
    agent.start_session()
    return agent


def _get_or_create_agent(session: Dict[str, Any], stream_callback) -> GeosAgent:
    if session["agent"] is None:
        session["agent"] = _create_agent(session, stream_callback)
    else:
        session["agent"].stream_callback = stream_callback
        session["agent"].client.stream_callback = stream_callback
    return session["agent"]


# ---------------------------------------------------------------------------
# File tree
# ---------------------------------------------------------------------------


def _build_tree(
    path: Path, base: Path, max_depth: int = 6, depth: int = 0
) -> Optional[Dict]:
    if depth > max_depth:
        return None
    try:
        stat = path.stat()
    except (PermissionError, OSError):
        return None

    node: Dict[str, Any] = {
        "name": path.name,
        "path": str(path.relative_to(base)),
        "type": "directory" if path.is_dir() else "file",
    }

    if path.is_file():
        node["size"] = stat.st_size
        node["modified"] = stat.st_mtime
    elif path.is_dir():
        children = []
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
            for child in entries:
                if child.name.startswith("."):
                    continue
                child_node = _build_tree(child, base, max_depth, depth + 1)
                if child_node is not None:
                    children.append(child_node)
        except PermissionError:
            pass
        node["children"] = children

    return node


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------

TERMINAL_EVENT_TYPES = {"done", "user_input_required", "step_limit", "error"}


async def _stream_agent_response(
    session_id: str, message: str, is_resume: bool
) -> AsyncGenerator[str, None]:
    session = _sessions.get(session_id)
    if not session:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
        return

    if not os.environ.get("OPENROUTER_API_KEY"):
        yield (
            f"data: {json.dumps({'type': 'error', 'message': 'OPENROUTER_API_KEY not set.'})}\n\n"
        )
        return

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def put(event: Dict[str, Any]) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def stream_callback(event_type: str, data: Any) -> None:
        put({"type": event_type, "data": data})

    agent = _get_or_create_agent(session, stream_callback)

    # Snapshot outputs directory to detect new files
    outputs_dir = Path(session["workspace"]) / "outputs"
    pre_existing: set = set()
    if outputs_dir.is_dir():
        pre_existing = {str(p) for p in outputs_dir.rglob("*") if p.is_file()}

    def run_agent() -> None:
        try:
            if is_resume and session.get("pending_input"):
                session["pending_input"] = None
                agent.resume_after_user_input(message)
            else:
                agent.step(message)
            put({"type": "done"})
        except UserInputRequired as e:
            session["pending_input"] = {
                "question": e.question,
                "choices": e.choices,
                "default": e.default,
            }
            put(
                {
                    "type": "user_input_required",
                    "question": e.question,
                    "choices": e.choices or [],
                }
            )
        except AgentTerminationException as e:
            if e.reason == "Maximum number of steps exceeded":
                put({"type": "step_limit", "max_steps": e.max_steps})
            else:
                # Conversational reply — text already streamed
                put({"type": "done"})
        except Exception as e:
            put({"type": "error", "message": str(e)})
        finally:
            put(None)  # sentinel

    future = loop.run_in_executor(_executor, run_agent)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=120)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                continue

            if event is None:
                break

            event_type = event.get("type")
            yield f"data: {json.dumps(event)}\n\n"

            if event_type in TERMINAL_EVENT_TYPES:
                break
    finally:
        if session.get("agent"):
            usage = session["agent"].client.get_token_usage()
            session["token_usage"] = usage
            yield f"data: {json.dumps({'type': 'token_usage', **usage})}\n\n"

        if outputs_dir.is_dir():
            new_files = [
                str(Path(p).relative_to(session["workspace"]))
                for p in outputs_dir.rglob("*")
                if Path(p).is_file() and str(p) not in pre_existing
            ]
            if new_files:
                yield f"data: {json.dumps({'type': 'new_files', 'files': new_files})}\n\n"

        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
        await future


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/models")
async def get_models():
    return {"models": AVAILABLE_MODELS}


@app.post("/api/sessions")
async def create_session(req: SessionConfig):
    session_id = str(uuid.uuid4())

    if req.workspace_path:
        workspace = Path(req.workspace_path).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
    else:
        workspace = Path(tempfile.mkdtemp(prefix="geophysicist_ai_"))

    (workspace / "inputs").mkdir(exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)

    _sessions[session_id] = {
        "id": session_id,
        "config": req,
        "workspace": str(workspace),
        "agent": None,
        "pending_input": None,
        "token_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }

    return {"session_id": session_id, "workspace_path": str(workspace)}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    session = _sessions.pop(session_id, None)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "workspace_path": session["workspace"],
        "pending_input": session.get("pending_input"),
        "token_usage": session.get("token_usage"),
    }


@app.post("/api/sessions/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    is_resume = session.get("pending_input") is not None

    return StreamingResponse(
        _stream_agent_response(session_id, req.message, is_resume),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.put("/api/sessions/{session_id}/workspace")
async def update_workspace(session_id: str, req: WorkspaceUpdateRequest):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    wp = Path(req.workspace_path).resolve()
    if not wp.is_dir():
        raise HTTPException(status_code=400, detail="Directory does not exist")

    (wp / "inputs").mkdir(exist_ok=True)
    (wp / "outputs").mkdir(exist_ok=True)
    session["workspace"] = str(wp)
    session["agent"] = None  # force recreation

    return {"workspace_path": str(wp)}


@app.get("/api/sessions/{session_id}/tree")
async def get_workspace_tree(
    session_id: str, path: str = Query(default="")
):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    base = Path(session["workspace"]).resolve()
    target = (base / path).resolve() if path else base

    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=403, detail="Access denied")

    tree = _build_tree(target, base)
    return {"tree": tree, "workspace": str(base)}


@app.get("/api/sessions/{session_id}/file")
async def get_file(session_id: str, path: str = Query(...)):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    base = Path(session["workspace"]).resolve()
    target = (base / path).resolve()

    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(str(target))


@app.get("/api/sessions/{session_id}/token-usage")
async def get_token_usage(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get("agent"):
        usage = session["agent"].client.get_token_usage()
        session["token_usage"] = usage

    return session.get(
        "token_usage",
        {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_key_set": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
