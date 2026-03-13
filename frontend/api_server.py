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
from types import SimpleNamespace
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
from geos_agent.convex_store import ConvexChatStore, ConvexStoreError
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
_chat_store = ConvexChatStore.from_env()

# Model info cache
_model_cache: Optional[List[Dict[str, Any]]] = None
_model_cache_time: float = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_token_usage() -> Dict[str, int]:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }


def _serialize_pending_agent_state(pending: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not pending:
        return None

    def _serialize_tool_call(tool_call: Any) -> Dict[str, Any]:
        return {
            "id": getattr(tool_call, "id", ""),
            "function": {
                "name": getattr(getattr(tool_call, "function", None), "name", ""),
                "arguments": getattr(getattr(tool_call, "function", None), "arguments", "") or "",
            },
        }

    exc = pending.get("exception")
    return {
        "exception": {
            "question": getattr(exc, "question", ""),
            "choices": getattr(exc, "choices", None),
            "default": getattr(exc, "default", None),
            "fields": getattr(exc, "fields", None),
            "allow_custom_input": getattr(exc, "allow_custom_input", None),
            "tool_name": getattr(exc, "tool_name", ""),
            "tool_call_id": getattr(exc, "tool_call_id", ""),
        },
        "tool_call": _serialize_tool_call(pending["tool_call"]),
        "remaining_tool_calls": [
            _serialize_tool_call(tool_call)
            for tool_call in pending.get("remaining_tool_calls", [])
        ],
        "step_state": pending.get("step_state", {}),
    }


def _deserialize_pending_agent_state(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not data:
        return None

    exc_data = data.get("exception", {})
    exc = UserInputRequired(
        question=exc_data.get("question", ""),
        choices=exc_data.get("choices"),
        default=exc_data.get("default"),
    )
    exc.fields = exc_data.get("fields")
    exc.allow_custom_input = exc_data.get("allow_custom_input")
    exc.tool_name = exc_data.get("tool_name", "")
    exc.tool_call_id = exc_data.get("tool_call_id", "")

    def _tool_call_ref(raw: Dict[str, Any]) -> Any:
        return SimpleNamespace(
            id=raw.get("id", ""),
            function=SimpleNamespace(
                name=raw.get("function", {}).get("name", ""),
                arguments=raw.get("function", {}).get("arguments", "") or "",
            ),
        )

    return {
        "exception": exc,
        "tool_call": _tool_call_ref(data.get("tool_call", {})),
        "remaining_tool_calls": [
            _tool_call_ref(raw) for raw in data.get("remaining_tool_calls", [])
        ],
        "step_state": data.get("step_state", {}),
    }


def _serialize_ui_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for message in messages:
        serialized.append(
            {
                "messageId": message.get("id") or str(uuid.uuid4()),
                "role": message.get("role", "assistant"),
                "timestamp": message.get("timestamp") or _utc_now(),
                "streaming": bool(message.get("streaming", False)),
                "partsJson": json.dumps(message.get("parts", [])),
            }
        )
    return serialized


def _build_session_payload(session: Dict[str, Any]) -> Dict[str, Any]:
    usage = session.get("token_usage") or _default_token_usage()
    enable_logging = bool(session["config"].enable_logging)
    payload = {
        "sessionId": session["id"],
        "name": session.get("name", ""),
        "createdAt": session.get("created_at") or _utc_now(),
        "lastMessageAt": _utc_now(),
        "messageCount": int(session.get("message_count", 0)),
        "workspacePath": session.get("workspace", ""),
        "configJson": json.dumps(session["config"].model_dump()),
        "pendingInputJson": (
            json.dumps(session.get("pending_input"))
            if session.get("pending_input") is not None
            and enable_logging
            else None
        ),
        "agentMessagesJson": (
            json.dumps(session.get("agent_messages", []))
            if enable_logging
            else None
        ),
        "agentPendingStateJson": (
            json.dumps(session.get("agent_pending_state"))
            if session.get("agent_pending_state") is not None
            and enable_logging
            else None
        ),
        "promptTokens": int(usage.get("prompt_tokens", 0)),
        "completionTokens": int(usage.get("completion_tokens", 0)),
        "totalTokens": int(usage.get("total_tokens", 0)),
        "turnPromptTokens": usage.get("turn_prompt_tokens"),
        "cachedTokens": usage.get("cached_tokens"),
        "cacheWriteTokens": usage.get("cache_write_tokens"),
        "contextTokensEst": usage.get("context_tokens_est"),
        "compactionThreshold": usage.get("compaction_threshold"),
        "messages": _serialize_ui_messages(session.get("ui_messages", [])) if enable_logging else [],
    }
    return {key: value for key, value in payload.items() if value is not None}


def _persist_session_state(session: Dict[str, Any]) -> None:
    if not _chat_store:
        return

    agent = session.get("agent")
    if agent is not None:
        session["agent_messages"] = agent.messages
        session["agent_pending_state"] = _serialize_pending_agent_state(
            getattr(agent, "_pending_user_input", None)
        )

    try:
        _chat_store.save_session_state(_build_session_payload(session))
    except ConvexStoreError as exc:
        print(f"Warning: failed to persist session {session['id']} to Convex: {exc}", file=sys.stderr)


def _session_summary_from_memory(session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": session["id"],
        "name": session.get("name", ""),
        "createdAt": session.get("created_at") or _utc_now(),
        "lastMessageAt": session.get("last_message_at") or _utc_now(),
        "messageCount": int(session.get("message_count", 0)),
    }


def _restore_session_from_store(session_id: str) -> Optional[Dict[str, Any]]:
    if not _chat_store:
        return None

    try:
        state = _chat_store.get_session_state(session_id)
    except ConvexStoreError as exc:
        print(f"Warning: failed to load session {session_id} from Convex: {exc}", file=sys.stderr)
        return None

    if not state:
        return None

    config_data = json.loads(state.get("configJson") or "{}")
    config = SessionConfig(**config_data)
    workspace = Path(state.get("workspacePath") or tempfile.mkdtemp(prefix="geophysicist_ai_")).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "inputs").mkdir(exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)

    ui_messages: List[Dict[str, Any]] = []
    for message in state.get("messages", []):
        ui_messages.append(
            {
                "id": message["id"],
                "role": message["role"],
                "parts": json.loads(message.get("partsJson") or "[]"),
                "timestamp": message["timestamp"],
                "streaming": bool(message.get("streaming", False)),
            }
        )

    restored = {
        "id": state["id"],
        "name": state.get("name", ""),
        "created_at": state.get("createdAt") or _utc_now(),
        "last_message_at": state.get("lastMessageAt") or _utc_now(),
        "config": config,
        "workspace": str(workspace),
        "agent": None,
        "pending_input": json.loads(state.get("pendingInputJson") or "null"),
        "message_count": int(state.get("messageCount", 0)),
        "token_usage": {
            "prompt_tokens": state.get("tokenUsage", {}).get("promptTokens", 0),
            "completion_tokens": state.get("tokenUsage", {}).get("completionTokens", 0),
            "total_tokens": state.get("tokenUsage", {}).get("totalTokens", 0),
            "turn_prompt_tokens": state.get("tokenUsage", {}).get("turnPromptTokens"),
            "cached_tokens": state.get("tokenUsage", {}).get("cachedTokens"),
            "cache_write_tokens": state.get("tokenUsage", {}).get("cacheWriteTokens"),
            "context_tokens_est": state.get("tokenUsage", {}).get("contextTokensEst"),
            "compaction_threshold": state.get("tokenUsage", {}).get("compactionThreshold"),
        },
        "ui_messages": ui_messages,
        "agent_messages": json.loads(state.get("agentMessagesJson") or "[]"),
        "agent_pending_state": _deserialize_pending_agent_state(
            json.loads(state.get("agentPendingStateJson") or "null")
        ),
    }
    _sessions[session_id] = restored
    return restored


def _get_session_or_restore(session_id: str) -> Optional[Dict[str, Any]]:
    return _sessions.get(session_id) or _restore_session_from_store(session_id)


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
TITLE_MODEL = "google/gemini-3.1-flash-lite-preview"

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
    enable_reasoning: bool = True
    enable_prompt_caching: bool = True
    prompt_cache_ttl: Optional[str] = None
    auto_compact_after_tokens: int = 100000
    temperature: float = 0.2
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    seed: Optional[int] = None
    max_output_tokens: int = 50000
    openrouter_extra_body: Optional[str] = None


class MessageRequest(BaseModel):
    message: str


class WorkspaceUpdateRequest(BaseModel):
    workspace_path: str


class TitleRequest(BaseModel):
    message: str


class RenameSessionRequest(BaseModel):
    name: str


# ---------------------------------------------------------------------------
# Agent helpers
# ---------------------------------------------------------------------------


def _create_agent(session: Dict[str, Any], stream_callback) -> GeosAgent:
    workspace_root = Path(session["workspace"]).resolve()
    cfg = session["config"]

    extra_body = {}
    if cfg.openrouter_extra_body:
        try:
            extra_body = json.loads(cfg.openrouter_extra_body)
        except (json.JSONDecodeError, TypeError):
            pass

    agent_config = AgentConfig(
        model=cfg.model,
        provider=cfg.provider or None,
        max_steps=cfg.max_steps,
        mode="interactive",
        enable_context_compaction=cfg.enable_context_compaction,
        reasoning=cfg.enable_reasoning,
        openrouter_prompt_caching=cfg.enable_prompt_caching,
        openrouter_prompt_cache_ttl=cfg.prompt_cache_ttl or None,
        context_compaction_trigger_tokens=cfg.auto_compact_after_tokens,
        temperature=cfg.temperature,
        top_p=cfg.top_p,
        frequency_penalty=cfg.frequency_penalty,
        presence_penalty=cfg.presence_penalty,
        seed=cfg.seed,
        max_tokens=cfg.max_output_tokens,
        openrouter_extra_body=extra_body,
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
        if session.get("agent_messages"):
            session["agent"].messages = session["agent_messages"]
        if session.get("agent_pending_state"):
            session["agent"]._pending_user_input = session["agent_pending_state"]
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
    session = _get_session_or_restore(session_id)
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
    session["last_message_at"] = _utc_now()

    user_message = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "parts": [{"type": "text", "content": message}],
        "timestamp": _utc_now(),
    }
    assistant_message = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "parts": [],
        "timestamp": _utc_now(),
        "streaming": True,
    }
    session.setdefault("ui_messages", []).extend([user_message, assistant_message])
    assistant_index = len(session["ui_messages"]) - 1
    assistant_parts: List[Dict[str, Any]] = []
    current_text = ""
    current_thinking = ""

    def flush_text() -> None:
        nonlocal current_text
        if current_text:
            assistant_parts.append({"type": "text", "content": current_text})
            current_text = ""

    def refresh_assistant(streaming: bool = True) -> None:
        snapshot = list(assistant_parts)
        if current_text:
            snapshot.append({"type": "text", "content": current_text})
        session["ui_messages"][assistant_index]["parts"] = snapshot
        session["ui_messages"][assistant_index]["timestamp"] = _utc_now()
        session["ui_messages"][assistant_index]["streaming"] = streaming

    workspace_root = Path(session["workspace"]).resolve()

    def snapshot_workspace_files() -> set[str]:
        if not workspace_root.is_dir():
            return set()
        return {str(p) for p in workspace_root.rglob("*") if p.is_file()}

    seen_files = snapshot_workspace_files()

    def collect_new_files() -> List[str]:
        nonlocal seen_files
        current_files = snapshot_workspace_files()
        new_files = sorted(current_files - seen_files)
        seen_files = current_files
        return [str(Path(p).relative_to(workspace_root)) for p in new_files]

    def run_agent() -> None:
        try:
            if is_resume and session.get("pending_input"):
                session["pending_input"] = None
                session["agent_pending_state"] = None
                agent.resume_after_user_input(message)
            else:
                agent.step(message)
            put({"type": "done"})
        except UserInputRequired as e:
            session["pending_input"] = {
                "question": e.question,
                "choices": e.choices,
                "default": e.default,
                "fields": getattr(e, "fields", None),
                "allow_custom_input": getattr(e, "allow_custom_input", None),
            }
            put(
                {
                    "type": "user_input_required",
                    "question": e.question,
                    "choices": e.choices or [],
                    "default": e.default,
                    "fields": getattr(e, "fields", None),
                    "allow_custom_input": getattr(e, "allow_custom_input", None),
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
            if event_type == "text":
                current_text += event.get("data", "")
                refresh_assistant(True)
            elif event_type == "thinking_start":
                flush_text()
                current_thinking = ""
            elif event_type == "thinking":
                current_thinking += event.get("data", "")
            elif event_type == "thinking_end":
                if current_thinking:
                    assistant_parts.append({"type": "thinking", "content": current_thinking})
                    current_thinking = ""
                refresh_assistant(True)
            elif event_type == "tool_start":
                flush_text()
                tool_data = event.get("data", {})
                assistant_parts.append(
                    {
                        "type": "tool_call",
                        "name": tool_data.get("name", ""),
                        "summary": tool_data.get("summary", ""),
                        "streaming": True,
                    }
                )
                refresh_assistant(True)
            elif event_type == "tool_result":
                tool_data = event.get("data", {})
                for idx in range(len(assistant_parts) - 1, -1, -1):
                    part = assistant_parts[idx]
                    if part.get("type") == "tool_call" and part.get("name") == tool_data.get("name"):
                        assistant_parts[idx] = {
                            **part,
                            "result": tool_data.get("result", ""),
                            "streaming": False,
                        }
                        break
                refresh_assistant(True)
            elif event_type == "tool_error":
                tool_data = event.get("data", {})
                for idx in range(len(assistant_parts) - 1, -1, -1):
                    part = assistant_parts[idx]
                    if part.get("type") == "tool_call" and part.get("name") == tool_data.get("name"):
                        assistant_parts[idx] = {
                            **part,
                            "error": tool_data.get("error", ""),
                            "streaming": False,
                        }
                        break
                refresh_assistant(True)
            elif event_type == "user_input_required":
                flush_text()
                pending_question = event.get("question", "")
                pending_choices = event.get("choices", []) or []
                session["pending_input"] = {
                    "question": pending_question,
                    "choices": pending_choices,
                    "default": session.get("pending_input", {}).get("default"),
                    "fields": event.get("fields"),
                    "allow_custom_input": event.get("allow_custom_input"),
                }
                assistant_parts.append(
                    {
                        "type": "question",
                        "content": pending_question,
                        "choices": pending_choices,
                        "default": event.get("default"),
                        "fields": event.get("fields"),
                        "allowCustomInput": event.get("allow_custom_input"),
                    }
                )
                refresh_assistant(False)
            elif event_type == "step_limit":
                flush_text()
                assistant_parts.append(
                    {
                        "type": "warning",
                        "content": f"Step limit reached ({event.get('max_steps', 0)} steps). You can continue the conversation.",
                    }
                )
                refresh_assistant(False)
            elif event_type == "error":
                flush_text()
                assistant_parts.append(
                    {"type": "error", "content": str(event.get("message", "Unknown error"))}
                )
                refresh_assistant(False)

            yield f"data: {json.dumps(event)}\n\n"

            if event_type in {"tool_result", "tool_error"}:
                new_files = collect_new_files()
                if new_files:
                    yield f"data: {json.dumps({'type': 'new_files', 'files': new_files})}\n\n"

            if event_type in TERMINAL_EVENT_TYPES:
                break
    finally:
        flush_text()
        refresh_assistant(False)

        if session.get("agent"):
            usage = session["agent"].client.get_token_usage()
            session["token_usage"] = usage
            session["agent_messages"] = session["agent"].messages
            session["agent_pending_state"] = _serialize_pending_agent_state(
                getattr(session["agent"], "_pending_user_input", None)
            )

            # Include context usage info
            context_info: Dict[str, Any] = {}
            agent_obj = session["agent"]
            if hasattr(agent_obj, "_last_compaction_stats") and agent_obj._last_compaction_stats:
                stats = agent_obj._last_compaction_stats
                context_info["context_tokens_est"] = stats.get("tokens_before", 0)
                context_info["compaction_threshold"] = stats.get("threshold", 100000)
            session["token_usage"] = {**usage, **context_info}

            yield f"data: {json.dumps({'type': 'token_usage', **usage, **context_info})}\n\n"

        # Update message count
        session["message_count"] = session.get("message_count", 0) + 1
        session["last_message_at"] = _utc_now()

        new_files = collect_new_files()
        if new_files:
            yield f"data: {json.dumps({'type': 'new_files', 'files': new_files})}\n\n"

        _persist_session_state(session)
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
        "name": "",
        "created_at": _utc_now(),
        "last_message_at": _utc_now(),
        "config": req,
        "workspace": str(workspace),
        "agent": None,
        "pending_input": None,
        "message_count": 0,
        "token_usage": _default_token_usage(),
        "ui_messages": [],
        "agent_messages": [],
        "agent_pending_state": None,
    }
    _persist_session_state(_sessions[session_id])

    return {"session_id": session_id, "workspace_path": str(workspace)}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    session = _sessions.pop(session_id, None)
    if session is None and _chat_store:
        stored = _restore_session_from_store(session_id)
        if stored is not None:
          _sessions.pop(session_id, None)
          session = stored
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if _chat_store:
        try:
            _chat_store.delete_session(session_id)
        except ConvexStoreError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    return {"deleted": session_id}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = _get_session_or_restore(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "workspace_path": session["workspace"],
        "name": session.get("name", ""),
        "created_at": session.get("created_at"),
        "last_message_at": session.get("last_message_at"),
        "pending_input": session.get("pending_input"),
        "token_usage": session.get("token_usage"),
        "messages": session.get("ui_messages", []),
        "config": session["config"].model_dump(),
        "message_count": session.get("message_count", 0),
    }


@app.post("/api/sessions/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest):
    session = _get_session_or_restore(session_id)
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
    session = _get_session_or_restore(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    wp = Path(req.workspace_path).resolve()
    if not wp.is_dir():
        raise HTTPException(status_code=400, detail="Directory does not exist")

    (wp / "inputs").mkdir(exist_ok=True)
    (wp / "outputs").mkdir(exist_ok=True)
    session["workspace"] = str(wp)
    session["last_message_at"] = _utc_now()
    session["agent"] = None  # force recreation
    _persist_session_state(session)

    return {"workspace_path": str(wp)}


@app.get("/api/sessions/{session_id}/tree")
async def get_workspace_tree(
    session_id: str, path: str = Query(default="")
):
    session = _get_session_or_restore(session_id)
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
    session = _get_session_or_restore(session_id)
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
    session = _get_session_or_restore(session_id)
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
    """List chat sessions, preferring live in-memory state over persisted snapshots."""
    sessions_by_id = {
        session["id"]: _session_summary_from_memory(session)
        for session in _sessions.values()
    }

    if _chat_store:
        try:
            for session in _chat_store.list_sessions():
                sessions_by_id.setdefault(session["id"], session)
        except ConvexStoreError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    sessions = list(sessions_by_id.values())
    sessions.sort(key=lambda item: item["lastMessageAt"], reverse=True)
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
                    "model": TITLE_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Generate a concise 2-5 word chat title from the user's first message. Reply with only the title, no quotes, numbering, or trailing punctuation.",
                        },
                        {"role": "user", "content": req.message[:500]},
                    ],
                    "max_tokens": 20,
                    "temperature": 0.2,
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
                    session = _get_session_or_restore(session_id)
                    if session:
                        session["name"] = title
                        session["last_message_at"] = _utc_now()
                        _persist_session_state(session)
                    return {"title": title}

        raise HTTPException(status_code=500, detail="Failed to generate title")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/sessions/{session_id}/rename")
async def rename_session(session_id: str, req: RenameSessionRequest):
    """Persist a user-supplied chat name."""
    cleaned = req.name.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    session = _get_session_or_restore(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session["name"] = cleaned
    session["last_message_at"] = _utc_now()
    _persist_session_state(session)
    return {"title": cleaned}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_key_set": bool(os.environ.get("OPENROUTER_API_KEY")),
        "convex_configured": bool(_chat_store and _chat_store.enabled),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6305, reload=False)
