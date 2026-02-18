"""
Geophysicist.ai - Web Frontend

Streamlit-based chat interface for the GEOS simulation agent.

Run with:
    uv run streamlit run frontend/app.py
"""

import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.user_io import UserInputRequired
from geos_agent.tools.utils import build_default_tools

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

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
    "anthropic/claude-sonnet-4-20250514",
    "google/gemini-2.5-flash",
    "openai/gpt-4o",
    "deepseek/deepseek-v3.2",
]

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

if "agent_model" not in st.session_state:
    st.session_state.agent_model = AVAILABLE_MODELS[0]

if "agent_max_steps" not in st.session_state:
    st.session_state.agent_max_steps = 100

# Default workspace: a fresh temp directory that persists for the session
if "workspace_path" not in st.session_state:
    _tmp = tempfile.mkdtemp(prefix="geophysicist_ai_")
    Path(_tmp, "inputs").mkdir()
    Path(_tmp, "outputs").mkdir()
    st.session_state.workspace_path = _tmp

# Pending user-input request from ask_user / confirm_action
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("\U0001f30d Geophysicist.ai")
    st.caption("AI Agent for GEOS Simulations")
    st.divider()

    model = st.selectbox("Model", AVAILABLE_MODELS, key="sidebar_model")
    max_steps = st.slider("Max steps per turn", 10, 200, 100, key="sidebar_max_steps")

    st.divider()

    # Workspace selector
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

    st.divider()

    if st.button("\U0001f5d1\ufe0f  New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent = None
        st.session_state.pending_input = None
        st.rerun()

    # Token usage
    if st.session_state.agent is not None:
        usage = st.session_state.agent.client.get_token_usage()
        if usage["total_tokens"] > 0:
            st.divider()
            st.caption("\U0001f4ca Token Usage")
            c1, c2 = st.columns(2)
            c1.metric("Input", f"{usage['prompt_tokens']:,}")
            c2.metric("Output", f"{usage['completion_tokens']:,}")

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def _create_agent() -> GeosAgent:
    """Create a fresh agent with current sidebar settings."""
    workspace_root = Path(st.session_state.workspace_path).resolve()
    tools = build_default_tools(workspace_root)
    config = AgentConfig(
        model=st.session_state.get("sidebar_model", AVAILABLE_MODELS[0]),
        max_steps=st.session_state.get("sidebar_max_steps", 100),
        mode="interactive",
    )
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
    return agent


def get_agent() -> GeosAgent:
    if st.session_state.agent is None:
        st.session_state.agent = _create_agent()
    return st.session_state.agent


# ---------------------------------------------------------------------------
# Helpers for rendering chat history
# ---------------------------------------------------------------------------


def _render_parts(parts: list) -> None:
    """Render a list of message parts (used for both live + history)."""
    for part in parts:
        ptype = part["type"]
        if ptype == "text":
            st.markdown(part["content"])
        elif ptype == "thinking":
            with st.expander("\U0001f4ad Reasoning", expanded=False):
                st.markdown(part["content"])
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
            st.info(f"\u2753 **Agent asked:** {part['content']}")
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
            st.markdown(msg["content"])

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
                _text_ph[0].markdown(_current_text[0])
                _parts.append({"type": "text", "content": _current_text[0]})
            _current_text[0] = ""
            _text_ph[0] = None

        def on_stream(event_type: str, data) -> None:
            if event_type == "text":
                if _text_ph[0] is None:
                    _text_ph[0] = container.empty()
                _current_text[0] += data
                _text_ph[0].markdown(_current_text[0] + "\u258c")

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
