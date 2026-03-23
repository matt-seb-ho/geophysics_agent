"""
Telegram bot interface for the GEOS geophysics agent.

Each Telegram chat gets its own GeosAgent session (conversation history
is kept per chat).  The agent runs in interactive mode so that ask_user
and confirm_action tool calls surface as natural Telegram messages rather
than blocking on stdin.

Usage:
    TELEGRAM_BOT_TOKEN=<token> uv run geos-telegram
    # or with options:
    uv run geos-telegram --workspace /path/to/workspace --model google/gemini-2.5-pro
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Set

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.user_io import UserInputRequired
from geos_agent.tools.utils import build_default_tools

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Telegram message length limit
# ---------------------------------------------------------------------------
_TG_MAX_LEN = 4096


# ---------------------------------------------------------------------------
# Per-chat session state
# ---------------------------------------------------------------------------


class _SessionState:
    """Holds one GeosAgent instance and auxiliary state for a single chat."""

    def __init__(self, agent: GeosAgent) -> None:
        self.agent = agent
        # Set when the last step raised UserInputRequired; cleared on resume.
        self.pending_input: Optional[UserInputRequired] = None
        # Serialize messages so two rapid texts don't corrupt agent history.
        self.lock: asyncio.Lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def _make_agent(workspace_root: Path, model: str, max_steps: int) -> GeosAgent:
    """Spin up a fresh GeosAgent in interactive mode with non-blocking IO."""
    tools = build_default_tools(workspace_root)
    config = AgentConfig(
        model=model,
        max_steps=max_steps,
        mode="interactive",
    )
    agent = GeosAgent(workspace_root=workspace_root, tools=tools, config=config)

    # Make ask_user / confirm_action raise UserInputRequired instead of
    # blocking on stdin — this is the same switch the web API uses.
    for t in agent.tools:
        if hasattr(t, "blocking"):
            t.blocking = False

    agent.start_session()
    return agent


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------


async def _send_chunks(update: Update, text: str) -> None:
    """Send a potentially long response, splitting at the Telegram limit."""
    text = text.strip()
    if not text:
        return
    for i in range(0, len(text), _TG_MAX_LEN):
        await update.message.reply_text(text[i : i + _TG_MAX_LEN])


async def _typing_loop(chat_id: int, bot, stop: asyncio.Event) -> None:
    """Keep sending 'typing' every 4 s until stop is set.

    Telegram drops the typing indicator after ~5 s, so we refresh it
    slightly before it expires — the same approach picoclaw uses for its
    Telegram channel.
    """
    try:
        while not stop.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(4)
    except Exception:
        pass  # Best-effort; don't crash the handler


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _sessions: Dict[int, _SessionState] = context.bot_data["sessions"]
    workspace_root: Path = context.bot_data["workspace_root"]
    model: str = context.bot_data["model"]
    max_steps: int = context.bot_data["max_steps"]

    loop = asyncio.get_event_loop()
    agent = await loop.run_in_executor(
        None, _make_agent, workspace_root, model, max_steps
    )
    _sessions[chat_id] = _SessionState(agent)

    await update.message.reply_text(
        "Hello! I'm the GEOS geophysics agent.\n\n"
        "Send me a natural-language description of the simulation you want to set up "
        "and I'll guide you through it interactively.\n\n"
        "Commands:\n"
        "  /start — start (or restart) a new session\n"
        "  /reset — same as /start\n"
        "  /help  — show this message"
    )


async def _cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_start(update, context)


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "GEOS Geophysics Agent — Telegram Interface\n\n"
        "Just send a message describing what you want to simulate. "
        "The agent will ask clarifying questions, create GEOS XML input files, "
        "run the simulation, and report back results.\n\n"
        "Commands:\n"
        "  /start or /reset — clear conversation and start fresh\n"
        "  /help            — show this message"
    )


# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    if not text:
        return

    # Allow-list check
    allowed_users: Optional[Set[int]] = context.bot_data.get("allowed_users")
    if allowed_users is not None:
        user_id = update.effective_user.id if update.effective_user else None
        if user_id not in allowed_users:
            logger.warning("Rejected message from user_id=%s", user_id)
            await update.message.reply_text(
                "Sorry, you are not authorised to use this bot."
            )
            return

    _sessions: Dict[int, _SessionState] = context.bot_data["sessions"]
    workspace_root: Path = context.bot_data["workspace_root"]
    model: str = context.bot_data["model"]
    max_steps: int = context.bot_data["max_steps"]

    # Auto-create session on first message
    if chat_id not in _sessions:
        loop = asyncio.get_event_loop()
        agent = await loop.run_in_executor(
            None, _make_agent, workspace_root, model, max_steps
        )
        _sessions[chat_id] = _SessionState(agent)

    state = _sessions[chat_id]

    async with state.lock:
        # Start persistent typing indicator
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            _typing_loop(chat_id, context.bot, stop_typing)
        )

        try:
            loop = asyncio.get_event_loop()

            if state.pending_input is not None:
                # Agent is waiting for a human answer from a previous ask_user
                # or confirm_action call.
                state.pending_input = None
                response = await loop.run_in_executor(
                    None, state.agent.resume_after_user_input, text
                )
            else:
                response = await loop.run_in_executor(
                    None, state.agent.step, text
                )

            stop_typing.set()
            await _send_chunks(update, response)

        except UserInputRequired as exc:
            state.pending_input = exc
            stop_typing.set()

            # Format the agent's question for Telegram
            question = exc.question.strip()
            if exc.choices:
                question += "\n\n" + "\n".join(f"  • {c}" for c in exc.choices)
            if exc.default:
                question += f"\n\n(default: {exc.default})"
            await _send_chunks(update, question)

        except AgentTerminationException as exc:
            state.pending_input = None
            stop_typing.set()
            short = str(exc).split("\n")[0]
            await update.message.reply_text(
                f"The agent stopped unexpectedly.\n\n{short}\n\n"
                "Use /reset to start a fresh session."
            )
        except Exception as exc:
            state.pending_input = None
            stop_typing.set()
            logger.exception("Unhandled error in message handler for chat %s", chat_id)
            await update.message.reply_text(
                f"An unexpected error occurred: {exc}\n\nUse /reset to try again."
            )
        finally:
            stop_typing.set()
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass


# ---------------------------------------------------------------------------
# Application builder
# ---------------------------------------------------------------------------


def build_app(
    token: str,
    workspace_root: Path,
    model: str,
    max_steps: int,
    allowed_users: Optional[Set[int]],
) -> Application:
    app = Application.builder().token(token).build()

    app.bot_data["sessions"] = {}
    app.bot_data["workspace_root"] = workspace_root
    app.bot_data["model"] = model
    app.bot_data["max_steps"] = max_steps
    app.bot_data["allowed_users"] = allowed_users  # None = allow everyone

    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("reset", _cmd_reset))
    app.add_handler(CommandHandler("help", _cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message))

    return app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser(
        description="GEOS geophysics agent — Telegram bot interface"
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root directory (default: current directory).",
    )
    parser.add_argument(
        "--model",
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model name (default: moonshotai/kimi-k2.5).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Maximum agent tool iterations per user turn (default: 100).",
    )
    parser.add_argument(
        "--allowed-users",
        default=None,
        help=(
            "Comma-separated list of Telegram user IDs allowed to use the bot. "
            "If omitted, everyone can use it. "
            "Can also be set via TELEGRAM_ALLOWED_USERS env var."
        ),
    )
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print(
            "Error: TELEGRAM_BOT_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve allow-list: CLI flag takes priority over env var
    raw_allowed = args.allowed_users or os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    allowed_users: Optional[Set[int]] = None
    if raw_allowed.strip():
        try:
            allowed_users = {int(uid.strip()) for uid in raw_allowed.split(",") if uid.strip()}
        except ValueError as e:
            print(f"Error parsing --allowed-users: {e}", file=sys.stderr)
            sys.exit(1)

    workspace_root = Path(args.workspace).resolve()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Starting GEOS Telegram bot (workspace=%s, model=%s)", workspace_root, args.model)
    if allowed_users:
        logger.info("Allow-list: %s", allowed_users)
    else:
        logger.info("No allow-list configured — all users accepted")

    app = build_app(
        token=token,
        workspace_root=workspace_root,
        model=args.model,
        max_steps=args.max_steps,
        allowed_users=allowed_users,
    )
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
