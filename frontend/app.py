"""
Geophysicist.ai - Web Frontend

Streamlit-based chat interface for the GEOS simulation agent.

Run with:
    uv run streamlit run frontend/app.py
"""

import os
import tempfile
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from geos_agent.agent_config import AgentConfig
from geos_agent.context_pruning import strip_message_refs
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.user_io import UserInputRequired
from geos_agent.tools.utils import build_default_tools

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
DEFAULT_SHARED_LOG_DIR = PROJECT_ROOT / "data" / "eval" / "jsonl_logs"
DEFAULT_LOCAL_LOG_DIR = PROJECT_ROOT / ".streamlit" / "jsonl_logs"

TOOL_ICONS = {
    "search_navigator": "\U0001f50d",
    "search_technical": "\U0001f52c",
    "search_web": "\U0001f310",
    "read_file": "\U0001f4d6",
    "write_file": "\u270d\ufe0f",
    "list_dir": "\U0001f4c1",
    "shell": "\U0001f4bb",
    "python_exec": "\U0001f40d",
    "fetch_code": "\U0001f4cb",
    "run_geos": "\U0001f680",
    "ask_user": "\u2753",
    "confirm_action": "\u2705",
}

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

MODEL_PRESET_OPTIONS = ["Custom"] + AVAILABLE_MODELS

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit command)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Geophysicist.ai",
    page_icon="\U0001f30d",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* Tighten up spacing */
    .stChatMessage { padding-top: 0.5rem; padding-bottom: 0.5rem; }

    /* Subtle tool-call styling */
    .stExpander { border-left: 3px solid #4a9eff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "agent_settings_snapshot" not in st.session_state:
    st.session_state.agent_settings_snapshot = None

if "agent_model" not in st.session_state:
    st.session_state.agent_model = AVAILABLE_MODELS[0]

if "agent_provider" not in st.session_state:
    st.session_state.agent_provider = ""

if "sidebar_model_name" not in st.session_state:
    st.session_state.sidebar_model_name = AVAILABLE_MODELS[0]

if "sidebar_provider" not in st.session_state:
    st.session_state.sidebar_provider = ""

if "sidebar_reasoning" not in st.session_state:
    st.session_state.sidebar_reasoning = True

if "sidebar_temperature" not in st.session_state:
    st.session_state.sidebar_temperature = 0.2

if "sidebar_top_p" not in st.session_state:
    st.session_state.sidebar_top_p = 1.0

if "sidebar_frequency_penalty" not in st.session_state:
    st.session_state.sidebar_frequency_penalty = 0.0

if "sidebar_presence_penalty" not in st.session_state:
    st.session_state.sidebar_presence_penalty = 0.0

if "sidebar_seed" not in st.session_state:
    st.session_state.sidebar_seed = ""

if "sidebar_max_tokens" not in st.session_state:
    st.session_state.sidebar_max_tokens = 50000

if "sidebar_openrouter_extra_body" not in st.session_state:
    st.session_state.sidebar_openrouter_extra_body = ""

if "sidebar_prompt_caching" not in st.session_state:
    st.session_state.sidebar_prompt_caching = True

if "sidebar_prompt_cache_ttl" not in st.session_state:
    st.session_state.sidebar_prompt_cache_ttl = "default"

if "sidebar_auto_compact_after_tokens" not in st.session_state:
    st.session_state.sidebar_auto_compact_after_tokens = 160000

if "agent_max_steps" not in st.session_state:
    st.session_state.agent_max_steps = 100

if "enable_conversation_logging" not in st.session_state:
    st.session_state.enable_conversation_logging = False

if "conversation_log_dir" not in st.session_state:
    st.session_state.conversation_log_dir = str(DEFAULT_SHARED_LOG_DIR)

if "last_conversation_log_path" not in st.session_state:
    st.session_state.last_conversation_log_path = ""

if "last_conversation_log_error" not in st.session_state:
    st.session_state.last_conversation_log_error = ""

if "token_usage" not in st.session_state:
    st.session_state.token_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
        "cache_write_tokens": 0,
    }

# Default workspace: a fresh temp directory that persists for the session
if "workspace_path" not in st.session_state:
    _tmp = tempfile.mkdtemp(prefix="geophysicist_ai_")
    Path(_tmp, "inputs").mkdir()
    Path(_tmp, "outputs").mkdir()
    st.session_state.workspace_path = _tmp

# Pending user-input request from ask_user / confirm_action
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None


def _normalize_model_preset(model_name: str) -> str:
    return model_name if model_name in AVAILABLE_MODELS else "Custom"


def _parse_seed(value: str) -> int | None:
    raw = value.strip()
    if not raw:
        return None
    return int(raw)


def _parse_openrouter_extra_body(raw_value: str) -> tuple[dict, str | None]:
    raw = raw_value.strip()
    if not raw:
        return {}, None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"Advanced OpenRouter JSON is invalid: {exc}"
    if not isinstance(parsed, dict):
        return {}, "Advanced OpenRouter JSON must be a JSON object."
    return parsed, None


def _get_sidebar_model_name() -> str:
    return (st.session_state.get("sidebar_model_name") or AVAILABLE_MODELS[0]).strip()


def _get_current_agent_settings() -> tuple[dict, str | None]:
    model_name = _get_sidebar_model_name()
    if not model_name:
        return {}, "Model name cannot be empty."

    try:
        seed = _parse_seed(st.session_state.get("sidebar_seed", ""))
    except ValueError:
        return {}, "Seed must be a whole number."

    extra_body, extra_body_error = _parse_openrouter_extra_body(
        st.session_state.get("sidebar_openrouter_extra_body", "")
    )
    if extra_body_error:
        return {}, extra_body_error

    settings = {
        "model": model_name,
        "provider": (st.session_state.get("sidebar_provider") or "").strip() or None,
        "reasoning": bool(st.session_state.get("sidebar_reasoning", True)),
        "temperature": float(st.session_state.get("sidebar_temperature", 0.2)),
        "top_p": float(st.session_state.get("sidebar_top_p", 1.0)),
        "frequency_penalty": float(
            st.session_state.get("sidebar_frequency_penalty", 0.0)
        ),
        "presence_penalty": float(
            st.session_state.get("sidebar_presence_penalty", 0.0)
        ),
        "seed": seed,
        "max_tokens": int(st.session_state.get("sidebar_max_tokens", 50000)),
        "max_steps": int(st.session_state.get("sidebar_max_steps", 100)),
        "prompt_caching": bool(st.session_state.get("sidebar_prompt_caching", True)),
        "prompt_cache_ttl": (
            None
            if st.session_state.get("sidebar_prompt_cache_ttl", "default") == "default"
            else st.session_state.get("sidebar_prompt_cache_ttl", "default")
        ),
        "auto_compact_after_tokens": int(
            st.session_state.get("sidebar_auto_compact_after_tokens", 160000)
        ),
        "openrouter_extra_body": extra_body,
    }
    return settings, None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("\U0001f30d Geophysicist.ai")
    st.caption("AI Agent for GEOS Simulations")
    st.divider()

    if "sidebar_model_preset" not in st.session_state:
        st.session_state.sidebar_model_preset = _normalize_model_preset(
            st.session_state.sidebar_model_name
        )
    st.selectbox(
        "Preset",
        MODEL_PRESET_OPTIONS,
        key="sidebar_model_preset",
        help="Pick a common model preset or switch to Custom for any OpenRouter model ID.",
    )
    if st.session_state.sidebar_model_preset != "Custom":
        st.session_state.sidebar_model_name = st.session_state.sidebar_model_preset
    else:
        st.text_input(
            "Model name",
            key="sidebar_model_name",
            placeholder="e.g. openai/gpt-5.3-codex",
            help="Exact OpenRouter model ID used for requests.",
        )
    with st.expander("Advanced model options", expanded=False):
        st.text_input(
            "Provider override",
            key="sidebar_provider",
            placeholder="e.g. baseten, novita, together",
            help="Route the request to a specific OpenRouter provider.",
        )
        st.checkbox(
            "Enable reasoning",
            key="sidebar_reasoning",
            help="Request reasoning tokens for models/providers that support them.",
        )
        st.checkbox(
            "Enable prompt caching",
            key="sidebar_prompt_caching",
            help=(
                "Use provider prompt caching where available. OpenAI, Moonshot, "
                "Grok, Groq, and DeepSeek cache implicitly; Anthropic and Gemini "
                "receive explicit cache hints from this client."
            ),
        )
        st.selectbox(
            "Prompt cache TTL",
            options=("default", "1h"),
            key="sidebar_prompt_cache_ttl",
            help="Anthropic cache TTL override. Most non-Anthropic providers ignore this.",
        )
        st.number_input(
            "Auto-compact after tokens",
            min_value=0,
            max_value=2_000_000,
            value=st.session_state.sidebar_auto_compact_after_tokens,
            step=10000,
            key="sidebar_auto_compact_after_tokens",
            help=(
                "Current prompt-context token threshold for local context "
                "compaction and stronger dynamic-pruning/compression nudges. "
                "Set to 0 to disable the threshold."
            ),
        )
        st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.sidebar_temperature,
            step=0.05,
            key="sidebar_temperature",
        )
        st.slider(
            "Top p",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.sidebar_top_p,
            step=0.05,
            key="sidebar_top_p",
        )
        st.slider(
            "Frequency penalty",
            min_value=-2.0,
            max_value=2.0,
            value=st.session_state.sidebar_frequency_penalty,
            step=0.1,
            key="sidebar_frequency_penalty",
        )
        st.slider(
            "Presence penalty",
            min_value=-2.0,
            max_value=2.0,
            value=st.session_state.sidebar_presence_penalty,
            step=0.1,
            key="sidebar_presence_penalty",
        )
        st.text_input(
            "Seed",
            key="sidebar_seed",
            placeholder="Optional integer",
            help="Optional deterministic seed for models that support it.",
        )
        st.number_input(
            "Max output tokens",
            min_value=1,
            max_value=200000,
            value=st.session_state.sidebar_max_tokens,
            step=1000,
            key="sidebar_max_tokens",
            help="Upper bound for generated output tokens.",
        )
        st.text_area(
            "Extra OpenRouter JSON",
            key="sidebar_openrouter_extra_body",
            height=140,
            placeholder='{"provider":{"allow_fallbacks":false},"transforms":["middle-out"]}',
            help=(
                "Optional JSON object merged into OpenRouter's extra request body. "
                "Use this for provider routing and other OpenRouter-specific flags "
                "not exposed above."
            ),
        )
        _, _advanced_error = _get_current_agent_settings()
        if _advanced_error:
            st.error(_advanced_error)
    _current_settings, _settings_error = _get_current_agent_settings()
    if (
        not _settings_error
        and st.session_state.agent is not None
        and st.session_state.agent_settings_snapshot != _current_settings
    ):
        st.info("Model changes apply on the next New Chat.")
    st.divider()
    max_steps = st.slider("Max steps per turn", 10, 200, 100, key="sidebar_max_steps")

    st.divider()
    enable_logging = st.checkbox(
        "Save conversation log (.jsonl)",
        key="sidebar_enable_logging",
        value=st.session_state.enable_conversation_logging,
        help=(
            "Write the structured conversation log after each turn in a format "
            "compatible with scripts/eval/compute_agent_metrics.py."
        ),
    )
    log_dir = st.text_input(
        "Log directory",
        key="sidebar_log_dir",
        value=st.session_state.conversation_log_dir,
        help="Directory for conversation logs.",
    )
    st.session_state.enable_conversation_logging = enable_logging
    st.session_state.conversation_log_dir = log_dir

    st.divider()

    new_workspace = st.text_input(
        "Workspace directory",
        value=st.session_state.workspace_path,
        help="Agent reads/writes files here. Defaults to a fresh temp folder.",
    )
    if new_workspace != st.session_state.workspace_path:
        wp = Path(new_workspace).resolve()
        if wp.is_dir():
            wp.joinpath("inputs").mkdir(exist_ok=True)
            wp.joinpath("outputs").mkdir(exist_ok=True)
            st.session_state.workspace_path = str(wp)
            st.session_state.agent = None  # recreate with new workspace
            st.rerun()
        else:
            st.error("Directory does not exist.")

    if st.session_state.enable_conversation_logging:
        _workspace_name = Path(st.session_state.workspace_path).resolve().name
        _log_name = f"{_workspace_name}.jsonl"
        st.caption(f"Log file name: `{_log_name}`")
        if st.session_state.last_conversation_log_path:
            st.caption(f"Last saved: `{st.session_state.last_conversation_log_path}`")
        if st.session_state.last_conversation_log_error:
            st.warning(st.session_state.last_conversation_log_error)

    st.divider()

    if st.button("\U0001f5d1\ufe0f  New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent = None
        st.session_state.pending_input = None
        st.session_state.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
            "cache_write_tokens": 0,
        }
        st.rerun()

    # Token usage (always visible)
    if st.session_state.agent is not None:
        usage = st.session_state.agent.client.get_token_usage()
        st.session_state.token_usage = {
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "cached_tokens": int(usage.get("cached_tokens", 0) or 0),
            "cache_write_tokens": int(usage.get("cache_write_tokens", 0) or 0),
        }
    elif not st.session_state.messages:
        st.session_state.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
            "cache_write_tokens": 0,
        }

    st.divider()
    _usage = st.session_state.token_usage
    _tok_c1, _tok_c2, _tok_c3 = st.columns(3)
    _tok_in_ph = _tok_c1.empty()
    _tok_out_ph = _tok_c2.empty()
    _tok_total_ph = _tok_c3.empty()
    _tok_in_ph.metric("Input", f"{_usage['prompt_tokens']:,}")
    _tok_out_ph.metric("Output", f"{_usage['completion_tokens']:,}")
    _tok_total_ph.metric("Total", f"{_usage['total_tokens']:,}")
    _cache_c1, _cache_c2 = st.columns(2)
    _cache_c1.metric("Cache Read", f"{_usage['cached_tokens']:,}")
    _cache_c2.metric("Cache Write", f"{_usage['cache_write_tokens']:,}")

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def _create_agent() -> GeosAgent:
    """Create a fresh agent with current sidebar settings."""
    workspace_root = Path(st.session_state.workspace_path).resolve()
    tools = build_default_tools(workspace_root)
    settings, settings_error = _get_current_agent_settings()
    if settings_error:
        raise ValueError(settings_error)
    config = AgentConfig(
        model=settings["model"],
        provider=settings["provider"],
        temperature=settings["temperature"],
        top_p=settings["top_p"],
        frequency_penalty=settings["frequency_penalty"],
        presence_penalty=settings["presence_penalty"],
        seed=settings["seed"],
        max_tokens=settings["max_tokens"],
        max_steps=settings["max_steps"],
        reasoning=settings["reasoning"],
        openrouter_prompt_caching=settings["prompt_caching"],
        openrouter_prompt_cache_ttl=settings["prompt_cache_ttl"],
        context_compaction_trigger_tokens=settings["auto_compact_after_tokens"],
        openrouter_extra_body=settings["openrouter_extra_body"],
        mode="interactive",
    )
    config.context_pruning.tools.settings.context_limit = settings["auto_compact_after_tokens"]
    agent = GeosAgent(
        workspace_root=workspace_root,
        tools=tools,
        config=config,
    )
    # Mark IO tools as non-blocking so they raise UserInputRequired
    # instead of calling input() on stdin.  The stream_callback is
    # wired up per-turn (after agent creation), so __init__'s
    # "if stream_callback" guard doesn't flip this for us.
    for t in agent.tools:
        if hasattr(t, "blocking"):
            t.blocking = False
    agent.start_session()
    st.session_state.agent_settings_snapshot = settings
    return agent


def get_agent() -> GeosAgent:
    if st.session_state.agent is None:
        st.session_state.agent = _create_agent()
    return st.session_state.agent


def _sanitize_log_stem(name: str) -> str:
    """Create a filesystem-safe stem for log filenames."""
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in name)
    return safe.strip("._") or "workspace"


def _resolve_log_dir(raw_dir: str) -> tuple[Path | None, str]:
    """Resolve a writable directory for conversation logs."""
    requested_dir = Path(raw_dir).expanduser() if raw_dir else DEFAULT_SHARED_LOG_DIR

    for candidate in (requested_dir, DEFAULT_LOCAL_LOG_DIR):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate.resolve(), ""
        except OSError:
            continue

    return None, (
        "Failed to save log: neither the configured log directory nor the local "
        f"fallback is writable. Tried `{requested_dir}` and `{DEFAULT_LOCAL_LOG_DIR}`."
    )


def _save_conversation_log_if_enabled(agent: GeosAgent) -> None:
    """Persist conversation log as JSON payload in a .jsonl file."""
    if not st.session_state.get("enable_conversation_logging", False):
        return

    raw_dir = st.session_state.get("conversation_log_dir", "").strip()
    log_dir, log_dir_error = _resolve_log_dir(raw_dir)
    if log_dir is None:
        st.session_state.last_conversation_log_error = log_dir_error
        st.session_state.last_conversation_log_path = ""
        return

    requested_dir = Path(raw_dir).expanduser() if raw_dir else DEFAULT_SHARED_LOG_DIR
    if requested_dir != log_dir:
        st.session_state.last_conversation_log_error = (
            f"Configured log directory is not writable; saving logs to `{log_dir}` instead."
        )

    workspace_name = Path(st.session_state.workspace_path).resolve().name
    file_stem = _sanitize_log_stem(workspace_name)
    log_path = log_dir / f"{file_stem}.jsonl"

    try:
        log_data = agent._get_conversation_log()
        with log_path.open("w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        st.session_state.last_conversation_log_path = str(log_path)
        if requested_dir == log_dir:
            st.session_state.last_conversation_log_error = ""
    except Exception as e:
        st.session_state.last_conversation_log_error = f"Failed to save log: {e}"


# ---------------------------------------------------------------------------
# Helpers for rendering chat history
# ---------------------------------------------------------------------------


def _render_parts(parts: list) -> None:
    """Render a list of message parts (used for both live + history)."""
    for part in parts:
        ptype = part["type"]
        if ptype == "text":
            st.markdown(strip_message_refs(part["content"]))
        elif ptype == "thinking":
            with st.expander("\U0001f4ad Reasoning", expanded=False):
                st.markdown(strip_message_refs(part["content"]))
        elif ptype == "tool_call":
            icon = TOOL_ICONS.get(part["name"], "\u2699\ufe0f")
            st.markdown(f"{icon} **{part['name']}** \u2014 _{part['summary']}_")
            result = part.get("result", "")
            if result:
                with st.expander("Result", expanded=False):
                    st.code(result[:3000], language="text")
        elif ptype == "tool_error":
            st.error(part["content"])
        elif ptype == "error":
            st.warning(part["content"])
        elif ptype == "question":
            st.info(f"\u2753 **Agent asked:** {strip_message_refs(part['content'])}")
            choices = part.get("choices")
            if choices:
                st.markdown("Choices: " + ", ".join(f"`{c}`" for c in choices))
        elif ptype == "image":
            file_path = part["path"]
            if os.path.isfile(file_path):
                st.image(file_path, caption=part.get("caption", ""))
        elif ptype == "dataframe":
            import pandas as pd

            file_path = part["path"]
            if os.path.isfile(file_path):
                try:
                    df = pd.read_csv(file_path)
                    st.caption(part.get("caption", ""))
                    st.dataframe(df, use_container_width=True)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Welcome screen
# ---------------------------------------------------------------------------

if not st.session_state.messages:
    st.markdown(
        """
# \U0001f30d Geophysicist.ai

I'm an AI assistant for **GEOS multiphysics simulations**. I can help you:

- \U0001f3d7\ufe0f **Create** XML input decks for various simulation types
- \U0001f50d **Search** GEOS documentation and examples
- \U0001f680 **Run** simulations and analyze results
- \U0001f4ca **Visualize** output data with Python scripts

**Try asking:**
> Create a basic hydraulic fracture simulation

> Search for examples of multiphase flow

> Help me set up a wellbore model with thermal effects
"""
    )

# ---------------------------------------------------------------------------
# Display chat history
# ---------------------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("parts"):
            _render_parts(msg["parts"])
        elif msg.get("content"):
            st.markdown(strip_message_refs(msg["content"]))

# ---------------------------------------------------------------------------
# Pending-question indicator
# ---------------------------------------------------------------------------

if st.session_state.pending_input:
    _pending = st.session_state.pending_input
    st.info(
        f"\u2753 **The agent is waiting for your answer:** {_pending['question']}"
    )

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

_chat_placeholder = (
    "Answer the agent's question\u2026"
    if st.session_state.pending_input
    else "Describe your GEOS simulation\u2026"
)

if prompt := st.chat_input(_chat_placeholder):
    # ---- Display & store user message ----
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append(
        {"role": "user", "parts": [{"type": "text", "content": prompt}]}
    )

    # ---- Verify API key ----
    if not os.environ.get("OPENROUTER_API_KEY"):
        with st.chat_message("assistant"):
            st.error(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your `.env` file and restart the app."
            )
        st.stop()

    # ---- Get agent ----
    agent = get_agent()

    # ---- Determine whether this is a fresh step or a resume ----
    is_resume = st.session_state.pending_input is not None

    # ---- Snapshot output files so we can detect new ones after the turn ----
    _outputs_dir = Path(st.session_state.workspace_path) / "outputs"
    _IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp"}
    _TABLE_EXTS = {".csv"}
    _pre_existing: set[str] = set()
    if _outputs_dir.is_dir():
        _pre_existing = {str(p) for p in _outputs_dir.rglob("*") if p.is_file()}

    # ---- Streaming state (mutable via closures) ----
    _parts: list = []
    _current_text: list = [""]  # single-element list so callback can mutate
    _thinking_text: list = [""]
    _text_ph: list = [None]  # current st.empty() placeholder for streaming text

    with st.chat_message("assistant"):
        container = st.container()

        # -- Callback wired into agent/client --

        def _finalize_text() -> None:
            """Freeze the current text block and reset for the next one."""
            if _text_ph[0] is not None and _current_text[0]:
                cleaned = strip_message_refs(_current_text[0])
                if cleaned:
                    _text_ph[0].markdown(cleaned)
                    _parts.append({"type": "text", "content": cleaned})
                else:
                    _text_ph[0].empty()
            _current_text[0] = ""
            _text_ph[0] = None

        def on_stream(event_type: str, data) -> None:
            if event_type == "text":
                if _text_ph[0] is None:
                    _text_ph[0] = container.empty()
                _current_text[0] += data
                cleaned = strip_message_refs(_current_text[0])
                _text_ph[0].markdown((cleaned + "\u258c") if cleaned else "")

            elif event_type == "thinking_start":
                _finalize_text()
                _thinking_text[0] = ""

            elif event_type == "thinking":
                _thinking_text[0] += data

            elif event_type == "thinking_end":
                if _thinking_text[0]:
                    with container.expander("\U0001f4ad Reasoning", expanded=False):
                        st.markdown(_thinking_text[0])
                    _parts.append({"type": "thinking", "content": _thinking_text[0]})
                _thinking_text[0] = ""

            elif event_type == "tool_start":
                _finalize_text()
                name = data["name"]
                summary = data["summary"]
                icon = TOOL_ICONS.get(name, "\u2699\ufe0f")
                container.markdown(f"{icon} **{name}** \u2014 _{summary}_")
                _parts.append(
                    {
                        "type": "tool_call",
                        "name": name,
                        "summary": summary,
                        "result": "",
                    }
                )

            elif event_type == "tool_result":
                name = data["name"]
                result = data.get("result", "")
                # Attach result to last matching tool_call part
                for p in reversed(_parts):
                    if p["type"] == "tool_call" and p["name"] == name:
                        p["result"] = result
                        break
                with container.expander(f"Result: {name}", expanded=False):
                    display = result[:3000]
                    if len(result) > 3000:
                        display += "\n\u2026 (truncated)"
                    st.code(display, language="text")

            elif event_type == "tool_error":
                name = data["name"]
                error = data["error"]
                container.error(f"Tool error ({name}): {error}")
                _parts.append({"type": "tool_error", "content": f"{name}: {error}"})

        # Wire callbacks (agent is long-lived; callbacks change per turn)
        agent.stream_callback = on_stream
        agent.client.stream_callback = on_stream

        # ---- Run agent step or resume ----
        try:
            if is_resume:
                st.session_state.pending_input = None
                agent.resume_after_user_input(prompt)
            else:
                agent.step(prompt)
            _finalize_text()

        except UserInputRequired as e:
            _finalize_text()
            # Save pending state for next user message
            st.session_state.pending_input = {
                "question": e.question,
                "choices": e.choices,
                "default": e.default,
            }
            # Show the question in the assistant's response
            container.info(f"\u2753 **Question:** {e.question}")
            if e.choices:
                container.markdown(
                    "Choices: " + ", ".join(f"`{c}`" for c in e.choices)
                )
            _parts.append(
                {
                    "type": "question",
                    "content": e.question,
                    "choices": e.choices,
                }
            )

        except AgentTerminationException as e:
            _finalize_text()
            # For "no_tool_calls" (conversational responses), the text was
            # already streamed. Only surface real problems.
            if e.reason == "Maximum number of steps exceeded":
                container.warning(
                    f"Reached step limit ({e.max_steps}). "
                    "You can continue the conversation."
                )
                _parts.append(
                    {
                        "type": "error",
                        "content": f"Step limit reached ({e.max_steps})",
                    }
                )

        except Exception as e:
            _finalize_text()
            container.error(f"Error: {e}")
            _parts.append({"type": "error", "content": str(e)})

    # ---- Display new output files (images, tables) created this turn ----
    if _outputs_dir.is_dir():
        new_files = sorted(
            p for p in _outputs_dir.rglob("*")
            if p.is_file() and str(p) not in _pre_existing
        )
        for fpath in new_files:
            caption = fpath.name
            if fpath.suffix.lower() in _IMAGE_EXTS:
                with st.chat_message("assistant"):
                    st.image(str(fpath), caption=caption)
                _parts.append({"type": "image", "path": str(fpath), "caption": caption})
            elif fpath.suffix.lower() in _TABLE_EXTS:
                import pandas as pd

                try:
                    df = pd.read_csv(fpath)
                    with st.chat_message("assistant"):
                        st.caption(caption)
                        st.dataframe(df, use_container_width=True)
                    _parts.append({"type": "dataframe", "path": str(fpath), "caption": caption})
                except Exception:
                    pass

    # ---- Persist assistant message ----
    st.session_state.messages.append({"role": "assistant", "parts": _parts})
    _save_conversation_log_if_enabled(agent)

    # ---- Refresh token usage immediately after the turn ----
    _live_usage = agent.client.get_token_usage()
    st.session_state.token_usage = {
        "prompt_tokens": int(_live_usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(_live_usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(_live_usage.get("total_tokens", 0) or 0),
        "cached_tokens": int(_live_usage.get("cached_tokens", 0) or 0),
        "cache_write_tokens": int(_live_usage.get("cache_write_tokens", 0) or 0),
    }
    _tok_in_ph.metric("Input", f"{st.session_state.token_usage['prompt_tokens']:,}")
    _tok_out_ph.metric("Output", f"{st.session_state.token_usage['completion_tokens']:,}")
    _tok_total_ph.metric("Total", f"{st.session_state.token_usage['total_tokens']:,}")
