"""
FastAPI backend for the GEOS Agent — Next.js interface.

Wraps GeosAgent with streaming SSE endpoints.
Run with: uvicorn frontend.api_server:app --reload --port 6305
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
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

# Session persistence
_SESSIONS_DIR = Path.home() / ".geos-agent"
_SESSIONS_FILE = _SESSIONS_DIR / "sessions.json"

# Model info cache
_model_cache: Optional[List[Dict[str, Any]]] = None
_model_cache_time: float = 0


def _load_session_metadata() -> List[Dict[str, Any]]:
    """Load session metadata from disk."""
    if _SESSIONS_FILE.exists():
        try:
            data = json.loads(_SESSIONS_FILE.read_text())
            return data.get("sessions", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save_session_metadata(sessions: List[Dict[str, Any]]) -> None:
    """Write session metadata to disk."""
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    _SESSIONS_FILE.write_text(json.dumps({"sessions": sessions}, indent=2))


def _upsert_session_meta(
    session_id: str,
    name: str = "",
    message_count: int = 0,
    created_at: Optional[str] = None,
) -> None:
    """Create or update session metadata on disk."""
    sessions = _load_session_metadata()
    now = datetime.now(timezone.utc).isoformat()
    existing = next((s for s in sessions if s["id"] == session_id), None)
    if existing:
        existing["lastMessageAt"] = now
        existing["messageCount"] = message_count or existing.get("messageCount", 0)
        if name:
            existing["name"] = name
    else:
        sessions.insert(
            0,
            {
                "id": session_id,
                "name": name,
                "createdAt": created_at or now,
                "lastMessageAt": now,
                "messageCount": message_count,
            },
        )
    _save_session_metadata(sessions)


async def _fetch_openrouter_models() -> List[Dict[str, Any]]:
    """Fetch model list from OpenRouter with context lengths."""
    global _model_cache, _model_cache_time
    # Cache for 1 hour
    if _model_cache and (time.time() - _model_cache_time < 3600):
        return _model_cache

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                model_map = {m["id"]: m.get("context_length", 128000) for m in data}
                result = []
                for mid in AVAILABLE_MODELS:
                    result.append(
                        {"id": mid, "context_length": model_map.get(mid, 128000)}
                    )
                _model_cache = result
                _model_cache_time = time.time()
                return result
    except Exception:
        pass

    # Fallback: return models without real context lengths
    return [{"id": mid, "context_length": 128000} for mid in AVAILABLE_MODELS]


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
    enable_context_compaction: bool = True


class MessageRequest(BaseModel):
    message: str


class WorkspaceUpdateRequest(BaseModel):
    workspace_path: str


class TitleRequest(BaseModel):
    message: str


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
        enable_context_compaction=cfg.enable_context_compaction,
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

            # Include context usage info
            context_info: Dict[str, Any] = {}
            agent_obj = session["agent"]
            if hasattr(agent_obj, "_last_compaction_stats") and agent_obj._last_compaction_stats:
                stats = agent_obj._last_compaction_stats
                context_info["context_tokens_est"] = stats.get("tokens_before", 0)
                context_info["compaction_threshold"] = stats.get("threshold", 100000)

            yield f"data: {json.dumps({'type': 'token_usage', **usage, **context_info})}\n\n"

        # Update message count
        session["message_count"] = session.get("message_count", 0) + 1
        _upsert_session_meta(session_id, message_count=session["message_count"])

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
    models = await _fetch_openrouter_models()
    return {"models": models}


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
        "message_count": 0,
        "token_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }

    _upsert_session_meta(session_id)

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


@app.get("/api/chat-sessions")
async def list_chat_sessions():
    """List all persisted chat sessions."""
    sessions = _load_session_metadata()
    return {"sessions": sessions}


@app.post("/api/sessions/{session_id}/generate-title")
async def generate_title(session_id: str, req: TitleRequest):
    """Generate a short title for a chat session from the first message."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not set")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-5-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Generate a concise 3-6 word title for this chat based on the user's first message. Reply with ONLY the title, no quotes or punctuation.",
                        },
                        {"role": "user", "content": req.message[:500]},
                    ],
                    "max_tokens": 20,
                },
            )
            if resp.status_code == 200:
                title = (
                    resp.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if title:
                    _upsert_session_meta(session_id, name=title)
                    return {"title": title}

        raise HTTPException(status_code=500, detail="Failed to generate title")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_key_set": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6305, reload=False)
