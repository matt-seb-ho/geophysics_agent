"""
Dynamic Cheatsheet — cross-session memory for the GEOS agent.

Inspired by the Stanford "Dynamic Cheatsheet" paper (DC-Cumulative variant).
After each agent run a curator LLM call reflects on the trajectory and rewrites
a persistent cheatsheet that is injected into future runs' system prompts.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

from geos_agent.api_client import OpenRouterClient

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

CHEATSHEET_TEMPLATE = """
{separator}
DYNAMIC CHEATSHEET - Lessons from Previous Runs
{separator}

The following cheatsheet was automatically curated from previous agent runs.
It contains verified patterns, common pitfalls, and effective strategies.
Consult it before starting work — it may save you from repeating past mistakes.

{content}

{separator}
END OF DYNAMIC CHEATSHEET
{separator}"""

# ---------------------------------------------------------------------------
# Curator prompt
# ---------------------------------------------------------------------------

CURATOR_PROMPT = """\
# GEOS AGENT CHEATSHEET CURATOR

You are the Cheatsheet Curator for a GEOS/GEOSX simulation agent. After each
agent run you analyse the full trajectory (user request, agent reasoning, tool
calls, tool results, errors, and final outcome) and produce an updated
cheatsheet that will be injected into future runs.

## Purpose
The cheatsheet is a living document that prevents the agent from repeating
resolved mistakes and helps it work more efficiently. It should contain only
verified, actionable insights — not speculation.

## Core Responsibilities
1. **Preserve** all useful content from the previous cheatsheet — anything not
   explicitly included in your output will be lost.
2. **Assess** whether the agent's run was successful before incorporating new
   entries. Do not record strategies from failed runs unless the *fix* is what
   you are recording.
3. **Add** new insights from the current trajectory: working XML patterns,
   errors encountered and how they were resolved, effective search queries,
   and workflow tips.
4. **Prune** entries that are redundant, outdated, or too specific to be
   reusable. Keep the cheatsheet under ~2500 words so it fits comfortably in
   the agent's context window.
5. **Track usage** — increment the count on entries that were relevant to this
   run, even if they weren't explicitly referenced.

## Cheatsheet Structure

Organise entries into these sections:

### 1. XML PATTERNS & SOLVER CONFIGURATIONS
Working XML structures, tag usage, attribute values, and solver setups that
produced successful simulations.

### 2. COMMON ERRORS & FIXES
GEOS errors encountered (error messages, stack traces) and their resolutions.
Include the exact error string when possible so the agent can pattern-match.

### 3. TOOL USAGE STRATEGIES
Effective RAG search queries, read_file patterns, shell commands, and
post-processing scripts that worked well.

### 4. GENERAL WORKFLOW STRATEGIES
High-level tips: when to use base/benchmark pattern, how to debug mesh issues,
how to iterate on failing simulations, etc.

## Entry Format

Use this format for each entry:

```
<entry>
<topic>[Short descriptive title]</topic>
<insight>
[Concise, actionable description of the pattern/fix/strategy.
Include exact XML snippets, error messages, or search queries when relevant.]
</insight>
<refs>[Run 1, Run 3, ...]</refs>
</entry>
** Count: N
```

## Output Format

Wrap your entire updated cheatsheet in `<cheatsheet>` tags:

```
<cheatsheet>
Version: N

## XML PATTERNS & SOLVER CONFIGURATIONS

<entry>...</entry>
** Count: N

## COMMON ERRORS & FIXES

<entry>...</entry>
** Count: N

## TOOL USAGE STRATEGIES

<entry>...</entry>
** Count: N

## GENERAL WORKFLOW STRATEGIES

<entry>...</entry>
** Count: N

</cheatsheet>
```

IMPORTANT: Any content from the previous cheatsheet that is not included in
your new `<cheatsheet>` block will be permanently lost.

-----

## PREVIOUS CHEATSHEET

{previous_cheatsheet}

-----

## CURRENT RUN TRAJECTORY

{trajectory}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_cheatsheet(path: Path) -> str:
    """Read the cheatsheet file and return its contents, or empty string."""
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8").strip()
        return content
    except Exception as e:
        print(f"Warning: Could not read cheatsheet at {path}: {e}", file=sys.stderr)
        return ""


def save_cheatsheet(path: Path, content: str) -> None:
    """Write the cheatsheet content to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _extract_cheatsheet_block(response: str, fallback: str) -> str:
    """Parse the <cheatsheet>...</cheatsheet> block from the curator's response."""
    match = re.search(
        r"<cheatsheet>(.*?)</cheatsheet>", response, re.DOTALL
    )
    if match:
        return match.group(1).strip()
    # If no tags found, return the full response as a fallback (the curator
    # may have omitted tags) — but only if it looks substantive.
    if len(response.strip()) > 100:
        return response.strip()
    return fallback


def _condense_trajectory(conversation_log: Dict[str, Any]) -> str:
    """Condense a conversation log into a compact trajectory summary.

    We include:
    - The user prompt in full
    - Each assistant message (truncated to 1500 chars)
    - Tool call names + argument summaries
    - Tool results (truncated to 800 chars)
    This keeps the curator's context manageable while preserving key details.
    """
    parts: list[str] = []

    # User prompt
    user_prompt = conversation_log.get("user_prompt", "")
    parts.append(f"## User Request\n{user_prompt}")

    # Walk through agent messages
    agent_messages = conversation_log.get("agent_messages", [])
    tool_responses = conversation_log.get("tool_responses", [])

    # Build a lookup of tool responses by call ID
    response_by_id: Dict[str, str] = {}
    for tr in tool_responses:
        tid = tr.get("tool_call_id", "")
        content = tr.get("content", "")
        response_by_id[tid] = content

    for i, msg in enumerate(agent_messages):
        content = msg.get("content", "") or ""
        truncated = content[:1500] + ("..." if len(content) > 1500 else "")
        parts.append(f"## Agent Message {i + 1}\n{truncated}")

        tool_calls = msg.get("tool_calls", [])
        for tc in tool_calls:
            tool_name = tc.get("tool_name", "unknown")
            args_raw = tc.get("arguments", "{}")
            # Summarise arguments
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                args_summary = json.dumps(args, ensure_ascii=False)[:300]
            except (json.JSONDecodeError, TypeError):
                args_summary = str(args_raw)[:300]

            tid = tc.get("id", "")
            result_raw = response_by_id.get(tid, "")
            result_summary = result_raw[:800] + ("..." if len(result_raw) > 800 else "")

            parts.append(
                f"### Tool Call: {tool_name}\n"
                f"Args: {args_summary}\n"
                f"Result: {result_summary}"
            )

    # Token usage summary
    usage = conversation_log.get("usage", {})
    summary = conversation_log.get("summary", {})
    parts.append(
        f"## Run Summary\n"
        f"Total agent messages: {summary.get('total_agent_messages', '?')}\n"
        f"Total tool calls: {summary.get('total_tool_calls', '?')}\n"
        f"Tokens used: {usage.get('total_tokens', '?')}"
    )

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def curate_cheatsheet(
    conversation_log: Dict[str, Any],
    current_cheatsheet: str,
    client: OpenRouterClient,
    model: str,
) -> str:
    """Run the curator LLM call and return the updated cheatsheet text.

    Args:
        conversation_log: Output of GeosAgent._get_conversation_log()
        current_cheatsheet: Current cheatsheet content (may be empty)
        client: OpenRouterClient instance (reuses the agent's client)
        model: Model ID to use for the curator call

    Returns:
        The updated cheatsheet text (content only, no wrapper template).
    """
    trajectory = _condense_trajectory(conversation_log)

    previous = current_cheatsheet if current_cheatsheet else "(empty — this is the first run)"

    prompt = CURATOR_PROMPT.format(
        previous_cheatsheet=previous,
        trajectory=trajectory,
    )

    messages = [{"role": "user", "content": prompt}]

    print("\n[Cheatsheet] Curating cheatsheet from run trajectory...", file=sys.stderr)

    # Use a non-streaming call for curation (simpler, no tool calls needed).
    # We go through the underlying OpenAI client directly.
    response = client.with_retry(
        lambda: client.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
            stream=False,
        ),
        operation_name="cheatsheet curation",
    )

    response_text = response.choices[0].message.content or ""
    new_cheatsheet = _extract_cheatsheet_block(response_text, fallback=current_cheatsheet)

    print("[Cheatsheet] Curation complete.", file=sys.stderr)
    return new_cheatsheet


def curate_and_save(
    conversation_log: Dict[str, Any],
    cheatsheet_path: Path,
    client: OpenRouterClient,
    model: str,
) -> None:
    """Convenience wrapper: load current cheatsheet, curate, and save."""
    current = load_cheatsheet(cheatsheet_path)
    updated = curate_cheatsheet(conversation_log, current, client, model)
    save_cheatsheet(cheatsheet_path, updated)
    print(f"[Cheatsheet] Saved to {cheatsheet_path}", file=sys.stderr)
