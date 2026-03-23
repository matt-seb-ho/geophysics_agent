# GEOS Geophysics Agent — Telegram Bot

This document describes the architecture, design choices, and setup instructions for the Telegram bot interface to the GEOS geophysics agent.

---

## Overview

The Telegram bot is the simplest way to interact with the agent: you just open a conversation in the Telegram app, describe the simulation you want, and exchange messages as if you were chatting. No browser required, no server to expose publicly beyond a single outbound HTTPS connection.

Under the hood every Telegram chat maps to a dedicated `GeosAgent` session, so each user (or group chat) gets fully isolated conversation history.

---

## Architecture

```
Telegram servers
        │  HTTPS (long polling)
        ▼
geos-telegram process
  ├── python-telegram-bot Application
  │       │  registered handlers
  │       ▼
  │   _handle_message(update)
  │       │
  │       ├── allow-list check
  │       │
  │       ├── look up / create _SessionState for this chat_id
  │       │
  │       ├── start _typing_loop background task
  │       │       (sends ChatAction.TYPING every 4 s while agent runs)
  │       │
  │       └── run_in_executor ──► GeosAgent.step()
  │                           or  GeosAgent.resume_after_user_input()
  │                                        │
  │                               tool-calling loop
  │                               (search, write XML, run GEOS…)
  │                                        │
  │                               returns str  ──► reply_text()
  │                               raises UserInputRequired ──► reply_text(question)
  │                               raises AgentTerminationException ──► reply_text(error)
  │
  └── per-chat _SessionState
          agent: GeosAgent          (interactive mode, non-blocking IO)
          pending_input: Optional   (set when UserInputRequired was raised)
          lock: asyncio.Lock        (serialises concurrent messages per chat)
```

### Key components

| Component | File | Role |
|---|---|---|
| `GeosAgent` | `src/geos_agent/geos_agent.py` | Core agent loop — unchanged |
| `build_default_tools` | `src/geos_agent/tools/utils.py` | Builds the full tool set |
| `UserInputRequired` | `src/geos_agent/tools/user_io.py` | Exception raised when the agent needs a human answer |
| `AgentTerminationException` | `src/geos_agent/geos_agent.py` | Raised on max-steps or unrecoverable failure |
| **`geos_telegram.bot`** | `src/geos_telegram/bot.py` | Telegram adapter (new) |

---

## Design choices

### Why Python, not Go?

Latency and memory footprint are not meaningful constraints here. The agent itself is Python, so staying in Python avoids a cross-language RPC layer and keeps the code simple. `python-telegram-bot` (v21+) is async-native and well-maintained.

### Why long polling, not webhooks?

Long polling requires zero infrastructure: no public IP, no TLS certificate, no reverse proxy. The bot process simply opens an outbound HTTPS connection to Telegram and waits for updates. Webhooks are faster and scale better but add operational complexity that is unnecessary for a single-instance deployment.

### Why one `GeosAgent` instance per chat?

`GeosAgent` stores conversation history in memory. Giving each chat its own instance provides natural isolation: user A's simulation context never bleeds into user B's conversation. The cost is memory proportional to the number of active chats, which is negligible for a research/personal deployment.

### Interactive mode and non-blocking IO

The agent is created with `mode="interactive"`, which enables the `ask_user` and `confirm_action` tools. These tools normally block on `stdin`; for the Telegram adapter they are switched to non-blocking mode (`t.blocking = False`), causing them to raise `UserInputRequired` instead.

When `UserInputRequired` is raised the handler:
1. Stores the exception on `state.pending_input`.
2. Sends the agent's question to the user as a Telegram message.
3. On the user's next message, calls `agent.resume_after_user_input(answer)` instead of `agent.step()`.

This is the same mechanism used by the web API (`frontend/api_server.py`).

### Typing indicator

Telegram's "typing…" bubble expires after ~5 seconds. A background coroutine (`_typing_loop`) re-sends `ChatAction.TYPING` every 4 seconds while the agent is running. It is cancelled (and the indicator disappears) as soon as the agent returns or raises. This mirrors the approach in picoclaw's Telegram channel.

### Per-chat asyncio lock

`GeosAgent` is not thread-safe: it writes to `self.messages` during every turn. If a user sends two messages in quick succession both would land in `_handle_message` concurrently. The `asyncio.Lock` on `_SessionState` ensures turns are processed sequentially for a given chat.

### Shared workspace

All chats share the same `workspace_root` (defaulting to the current directory). Generated XML files land in `data/inputs/` and simulation outputs in `data/outputs/`. For multi-user deployments where isolation matters, run separate bot processes pointing at different workspace roots.

---

## Setup instructions

### 1. Prerequisites

- Python 3.10+, `uv` installed.
- The geophysics agent repo checked out and dependencies installed (`uv sync`).
- A compiled GEOS-X binary (set `GEOSX_EXECUTABLE` in `.env`).
- An OpenRouter API key (set `OPENROUTER_API_KEY` in `.env`).

### 2. Create a Telegram bot

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts to choose a name and username.
3. BotFather will give you a token like `123456789:ABCdef…`. Copy it.

### 3. Configure environment

Add the token to your `.env` file (or export it in your shell):

```bash
# .env
TELEGRAM_BOT_TOKEN=123456789:ABCdef…
OPENROUTER_API_KEY=sk-or-…
GEOSX_EXECUTABLE=/path/to/geosx
```

Optionally restrict access to specific Telegram user IDs:

```bash
# Find your user ID by messaging @userinfobot in Telegram
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

### 4. Install dependencies

```bash
uv sync
```

This pulls in `python-telegram-bot>=21.0` along with the rest of the project dependencies.

### 5. Run the bot

```bash
uv run geos-telegram
```

With options:

```bash
uv run geos-telegram \
  --workspace /path/to/workspace \
  --model "google/gemini-2.5-pro" \
  --max-steps 150 \
  --allowed-users 123456789
```

Full option reference:

| Flag | Default | Description |
|---|---|---|
| `--workspace` | `.` (current dir) | Workspace root; XML files land in `<workspace>/data/inputs/` |
| `--model` | `moonshotai/kimi-k2.5` | OpenRouter model |
| `--max-steps` | `100` | Maximum tool iterations per user turn |
| `--allowed-users` | *(everyone)* | Comma-separated Telegram user IDs; overrides `TELEGRAM_ALLOWED_USERS` |

### 6. Talk to the bot

Open the bot in Telegram (search by the username you chose) and send it a message like:

> Set up a single-phase flow simulation on a 10×10×10 mesh with a pressure-driven boundary condition.

The agent will ask clarifying questions, create the XML input file, run GEOS, and report the outcome — all via Telegram messages.

Use `/reset` any time to clear the session and start fresh.

### 7. Running as a background service (optional)

```bash
# Using systemd (Linux)
cat > /etc/systemd/system/geos-telegram.service << 'EOF'
[Unit]
Description=GEOS Geophysics Agent Telegram Bot
After=network.target

[Service]
WorkingDirectory=/path/to/geophysics_agent
EnvironmentFile=/path/to/geophysics_agent/.env
ExecStart=/path/to/uv run geos-telegram
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now geos-telegram
```

Or simply run in a `tmux` or `screen` session for lightweight deployments.

---

## Comparison with existing UIs

| | CLI (`geos-agent`) | Web UI (Next.js + FastAPI) | Telegram bot |
|---|---|---|---|
| **Setup** | Just a terminal | Node + Python servers, browser | Bot token + `geos-telegram` |
| **Access** | Local machine only | Browser on any device | Telegram app on any device |
| **Streaming** | Token-by-token stdout | SSE to browser | Full response per message |
| **Session persistence** | Per invocation | Convex backend | In-process (lost on restart) |
| **Multi-user** | No | Yes (session IDs) | Yes (one agent per chat) |
| **Interactive Q&A** | Blocking stdin | Modal dialogs | Natural chat turn |
