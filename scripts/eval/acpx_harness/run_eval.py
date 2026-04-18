#!/usr/bin/env python3
"""
Docker-based eval harness for comparing claude_code and cursor_composer2 agents
on GEOS XML authoring tasks via acpx.

Usage:
    # Run all tasks for both agents under experiment_run1
    python run_eval.py --run experiment_run1

    # Specific agents only
    python run_eval.py --run experiment_run1 --agents claude_code

    # Include only specific tasks
    python run_eval.py --run experiment_run1 --include TutorialDeadOilEgg ExampleEDPWellbore

    # Exclude specific tasks
    python run_eval.py --run experiment_run1 --exclude TutorialDeadOilEgg

    # Override the experiments source directory
    python run_eval.py --run experiment_run1 --experiments-dir /path/to/my/tasks

    # Dry run (prints docker commands without executing)
    python run_eval.py --run experiment_run1 --dry-run

    # Adjust concurrency and timeout
    python run_eval.py --run experiment_run1 --workers 4 --timeout 900

Build the Docker image first:
    docker build -t geos-eval scripts/eval/acpx_harness/

Expected layout after a run:
    /home/brianliu/data/eval/
    ├── claude_code/
    │   └── experiment_run1/
    │       └── <task>/
    │           ├── inputs/          ← agent-generated XML files
    │           ├── outputs/         ← agent-generated outputs
    │           ├── acpx_output.json ← stdout from acpx
    │           ├── stderr.txt       ← stderr from acpx
    │           └── exit_code.txt    ← process exit code
    └── cursor_composer2/
        └── experiment_run1/
            └── <task>/
                └── ...

To evaluate results afterwards, use batch_lxml_evaluate.py:
    uv run python scripts/eval/batch_lxml_evaluate.py \\
        --experiments-dir /home/brianliu/data/eval/claude_code/experiment_run1 \\
        --ground-truth-dir /home/brianliu/data/eval/experiments_gt \\
        --results-dir /home/brianliu/data/eval/claude_code_results/experiment_run1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
EXPERIMENTS_DIR = DATA_DIR / "eval" / "experiments"
GROUND_TRUTH_DIR = DATA_DIR / "eval" / "experiments_gt"
GEOS_LIB_DIR = DATA_DIR / "GEOS"
# Temp copies of GEOS live here (same filesystem as GEOS_LIB_DIR so hardlinks work)
TEMP_GEOS_PARENT = DATA_DIR / "eval" / "tmp_geos"
DOCKER_IMAGE = "geos-eval"
DEFAULT_PLUGIN_DIR = Path("/home/brianliu/repo3")
DEFAULT_VECTOR_DB_DIR = Path("/data/shared/geophysics_agent_data/data/vector_db")
DEFAULT_GEOS_PRIMER_PATH = Path(
    "/home/brianliu/geophys-embodied-agent-framework/modules/profile/GEOS_PRIMER.md"
)
DEFAULT_CLAUDE_MODEL = "minimax/minimax-m2.7"
CONTAINER_PLUGIN_DIR = Path("/plugins/repo3")
CONTAINER_VECTOR_DB_DIR = Path("/data/shared/geophysics_agent_data/data/vector_db")
CONTAINER_MCP_CONFIG_PATH = Path("/workspace/claude_mcp_config.json")
CONTAINER_GEOS_PRIMER_PATH = Path("/workspace/GEOS_PRIMER.md")
RAG_TOOL_NAMES = {"search_navigator", "search_schema", "search_technical"}
PSEUDO_TOOL_RE = re.compile(r"<invoke\s+name=[\"']([^\"']+)[\"']", re.IGNORECASE)
NATIVE_CLAUDE_TOOLS = "default"
STOP_REQUESTED = threading.Event()
ACTIVE_PROCESS_LOCK = threading.Lock()
ACTIVE_PROCESSES: dict[int, subprocess.Popen[str]] = {}

# ---------------------------------------------------------------------------
# Agent definitions
# acpx_name: the agent identifier passed to `acpx <agent> exec`
# results_dir: where per-task workspaces land on the host
# api_key_env: environment variable name for the agent's API key
# ---------------------------------------------------------------------------

AGENTS: dict[str, dict] = {
    "claude_code": {
        "runner": "acpx",
        "acpx_name": "claude",
        "results_dir": DATA_DIR / "eval" / "claude_code",
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": None,  # passed via ANTHROPIC_API_KEY; model set by claude itself
    },
    "claude_code_repo3_plugin": {
        "runner": "claude_native",
        "results_dir": DATA_DIR / "eval" / "claude_code_repo3_plugin",
        "api_key_env": "ANTHROPIC_AUTH_TOKEN",
        "model": DEFAULT_CLAUDE_MODEL,
        "requires_rag": True,
    },
    "cursor_composer2": {
        "runner": "acpx",
        "acpx_name": "cursor",
        "results_dir": DATA_DIR / "eval" / "cursor_composer2",
        "api_key_env": "CURSOR_API_KEY",
        "model": "composer-2",
    },
}

DEFAULT_TIMEOUT = 600  # seconds per task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_agents_md() -> str:
    path = SCRIPT_DIR / "AGENTS.md"
    if not path.exists():
        raise FileNotFoundError(f"AGENTS.md not found at {path}")
    return path.read_text()


def load_task_instructions(task_dir: Path) -> str:
    path = task_dir / "instructions.txt"
    if not path.exists():
        raise FileNotFoundError(f"instructions.txt not found in {task_dir}")
    return path.read_text()


def build_prompt(agents_context: str, task_instructions: str) -> str:
    return (
        f"{agents_context}\n\n"
        "--- BEGIN SIMULATION SPECIFICATION ---\n"
        f"{task_instructions.strip()}\n"
        "--- END SIMULATION SPECIFICATION ---"
    )


def prepend_geos_primer_instruction(prompt: str) -> str:
    return (
        f"First action: use the Read tool to read {CONTAINER_GEOS_PRIMER_PATH}. "
        "Use it as the high-level orientation before using GEOS documentation, "
        "examples, schema, RAG tools, or writing XML.\n"
        "Use only real tool calls exposed by the runtime. Do not print XML-style "
        "<invoke> blocks, <parameter> blocks, or minimax:tool_call wrappers; those "
        "are text and will not execute. To create files, use the actual Write, Edit, "
        "or Bash tools exposed by the runtime, and write only under /workspace/inputs.\n\n"
        f"{prompt}"
    )


def redact_command_for_display(cmd: list[str]) -> str:
    redacted: list[str] = []
    secret_markers = ("KEY=", "TOKEN=", "SECRET=", "PASSWORD=")
    for token in cmd:
        if any(marker in token for marker in secret_markers):
            key = token.split("=", 1)[0]
            redacted.append(f"{key}=<redacted>")
        else:
            redacted.append(token)
    return " ".join(redacted)


# ---------------------------------------------------------------------------
# Restriction helpers (mirrors run_experiments_no_geos_parallel.py pattern)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Filtered GEOS copy
#
# Creates a per-task hardlinked copy of GEOS_LIB_DIR with restricted files
# removed.  Hardlinks are instantaneous and use no extra disk space when both
# paths are on the same filesystem (TEMP_GEOS_PARENT should live under the
# same mount as GEOS_LIB_DIR).  Falls back to a real copy if they differ.
# ---------------------------------------------------------------------------

def collect_ground_truth_xml_filenames(gt_experiment_dir: Path) -> list[str]:
    """Return sorted list of XML basenames under one ground-truth experiment directory."""
    if not gt_experiment_dir.exists():
        return []
    return sorted({p.name.lower() for p in gt_experiment_dir.rglob("*.xml") if p.is_file()})


def create_filtered_geos_copy(
    geos_src: Path,
    blocked_xml_basenames: set[str],
    tmp_parent: Path,
    blocked_rst_relpaths: set[str] | None = None,
) -> Path:
    """Hardlink-copy geos_src into a fresh temp dir, omitting blocked files.

    Returns the path of the copy (suitable for use as a Docker bind-mount
    source).  Its parent directory should be passed to cleanup_filtered_geos_copy
    when the experiment finishes.

    Args:
        geos_src: Original GEOS library directory.
        blocked_xml_basenames: Lowercased XML basenames to exclude (e.g. 'deadoil_base.xml').
        tmp_parent: Directory under which the temp copy is created.  Should be
            on the same filesystem as geos_src for hardlinks to work.
        blocked_rst_relpaths: Optional set of GEOS-relative RST paths to exclude
            (e.g. 'src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst').
    """
    tmp_parent.mkdir(parents=True, exist_ok=True)
    # mkdtemp creates the unique parent dir; copytree fills geos/ inside it.
    tmp_dir = Path(tempfile.mkdtemp(dir=tmp_parent, prefix="geos_eval_"))
    geos_dest = tmp_dir / "geos"

    blocked_xml_lower = {n.lower() for n in blocked_xml_basenames}
    blocked_rst_lower = {p.replace("\\", "/").lower() for p in (blocked_rst_relpaths or set())}

    def _ignore(src_dir: str, names: list[str]) -> set[str]:
        skipped: set[str] = set()
        for name in names:
            if name.lower() in blocked_xml_lower:
                skipped.add(name)
                continue
            if blocked_rst_lower:
                try:
                    rel = (Path(src_dir) / name).relative_to(geos_src)
                    if str(rel).replace("\\", "/").lower() in blocked_rst_lower:
                        skipped.add(name)
                except ValueError:
                    pass
        return skipped

    def _hardlink_or_copy(src: str, dst: str) -> None:
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)

    shutil.copytree(
        geos_src, geos_dest,
        ignore=_ignore,
        copy_function=_hardlink_or_copy,
        symlinks=True,
    )
    return geos_dest


def cleanup_filtered_geos_copy(geos_copy: Path) -> None:
    """Remove the temp directory created by create_filtered_geos_copy."""
    shutil.rmtree(geos_copy.parent, ignore_errors=True)


def create_runtime_vector_db_copy(vector_db_src: Path, result_dir: Path) -> Path:
    """Create a writable per-task ChromaDB copy.

    ChromaDB opens its sqlite backing files in a way that can write lock files
    even for read-oriented queries, so the container cannot mount the shared DB
    read-only.  Copying keeps the shared source untouched while allowing each
    parallel task to run independently.
    """
    vector_db_dest = result_dir / ".vector_db_runtime"
    if vector_db_dest.exists():
        shutil.rmtree(vector_db_dest)
    shutil.copytree(vector_db_src, vector_db_dest, symlinks=True)
    return vector_db_dest


def copy_geos_primer(geos_primer_path: Path, result_dir: Path) -> Path:
    primer_dest = result_dir / CONTAINER_GEOS_PRIMER_PATH.name
    shutil.copy2(geos_primer_path, primer_dest)
    return primer_dest


# ---------------------------------------------------------------------------
# Claude Code native runner helpers
# ---------------------------------------------------------------------------

def _safe_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    tmp_path.replace(path)


def _register_process(proc: subprocess.Popen[str]) -> None:
    with ACTIVE_PROCESS_LOCK:
        ACTIVE_PROCESSES[proc.pid] = proc


def _unregister_process(proc: subprocess.Popen[str]) -> None:
    with ACTIVE_PROCESS_LOCK:
        ACTIVE_PROCESSES.pop(proc.pid, None)


def stop_active_processes(*, grace_seconds: float = 5.0) -> None:
    STOP_REQUESTED.set()
    with ACTIVE_PROCESS_LOCK:
        processes = list(ACTIVE_PROCESSES.values())

    for proc in processes:
        if proc.poll() is None:
            proc.terminate()

    deadline = time.time() + grace_seconds
    for proc in processes:
        remaining = max(0.0, deadline - time.time())
        if proc.poll() is not None:
            continue
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            if proc.poll() is None:
                proc.kill()


def _tool_name_base(name: str) -> str:
    return name.rsplit("__", 1)[-1]


def _is_rag_tool(name: str) -> bool:
    base = _tool_name_base(name)
    return base in RAG_TOOL_NAMES or any(tool in name for tool in RAG_TOOL_NAMES)


def _is_repo3_plugin_tool(name: str) -> bool:
    return "repo3" in name or "geos-rag" in name or _is_rag_tool(name)


def _extract_tool_calls(value: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            node_type = str(node.get("type", ""))
            name = node.get("name") or node.get("tool_name") or node.get("toolName")
            if isinstance(name, str) and "tool" in node_type.lower():
                calls.append({"name": name, "input": node.get("input") or {}})
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return calls


def _string_values(value: Any) -> list[str]:
    values: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, str):
            values.append(node)
        elif isinstance(node, dict):
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return values


def _is_geos_primer_read(tool_call: dict[str, Any]) -> bool:
    name = _tool_name_base(str(tool_call.get("name", ""))).lower()
    input_payload = tool_call.get("input") or {}
    strings = _string_values(input_payload)

    if name == "read":
        return any(Path(text).name == CONTAINER_GEOS_PRIMER_PATH.name for text in strings)

    if name == "bash":
        read_commands = ("cat", "sed", "head", "tail", "less", "more", "rg", "grep")
        return any(
            CONTAINER_GEOS_PRIMER_PATH.name in text
            and any(command in text for command in read_commands)
            for text in strings
        )

    return False


def _extract_text_fragments(value: Any) -> list[dict[str, str]]:
    fragments: list[dict[str, str]] = []

    def role_for(node: dict[str, Any]) -> str:
        cursor: Any = node
        while isinstance(cursor, dict):
            message = cursor.get("message")
            if isinstance(message, dict) and isinstance(message.get("role"), str):
                return message["role"]
            cursor = cursor.get("_parent")
        return ""

    def visit(node: Any, parent: dict[str, Any] | None = None) -> None:
        if isinstance(node, dict):
            if parent is not None:
                node = {**node, "_parent": parent}
            if node.get("type") == "text" and isinstance(node.get("text"), str):
                text = node["text"].strip()
                if text:
                    fragments.append({"role": role_for(node), "text": text})
            elif isinstance(node.get("result"), str):
                text = node["result"].strip()
                if text:
                    fragments.append({"role": str(node.get("type") or "result"), "text": text})
            for key, child in node.items():
                if key != "_parent":
                    visit(child, node)
        elif isinstance(node, list):
            for child in node:
                visit(child, parent)

    visit(value)
    return fragments


def _extract_mcp_server_statuses(value: Any) -> dict[str, str]:
    statuses: dict[str, str] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            servers = node.get("mcp_servers")
            if isinstance(servers, list):
                for server in servers:
                    if not isinstance(server, dict):
                        continue
                    name = server.get("name")
                    status = server.get("status")
                    if isinstance(name, str) and isinstance(status, str):
                        statuses[name] = status
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return statuses


def _extract_pseudo_tool_invocations(text: str) -> list[str]:
    return [match.group(1) for match in PSEUDO_TOOL_RE.finditer(text)]


def _new_tool_counts() -> dict[str, Any]:
    return {
        "total_tool_calls": 0,
        "per_tool_counts": {},
        "plugin_tool_calls": 0,
        "rag_tool_calls": 0,
        "rag_tool_counts": {name: 0 for name in sorted(RAG_TOOL_NAMES)},
        "rag_requirement_met": False,
        "rag_mcp_unavailable": False,
        "rag_pseudo_invocations": 0,
        "pseudo_tool_calls": 0,
        "pseudo_tool_counts": {},
        "mcp_server_statuses": {},
        "primer_read": False,
        "primer_read_tool_calls": 0,
    }


def _record_tool_call(counts: dict[str, Any], tool_name: str) -> None:
    per_tool = counts["per_tool_counts"]
    per_tool[tool_name] = per_tool.get(tool_name, 0) + 1
    counts["total_tool_calls"] += 1

    if _is_repo3_plugin_tool(tool_name):
        counts["plugin_tool_calls"] += 1

    if _is_rag_tool(tool_name):
        base = _tool_name_base(tool_name)
        rag_tool_counts = counts["rag_tool_counts"]
        if base not in rag_tool_counts:
            rag_tool_counts[base] = 0
        rag_tool_counts[base] += 1
        counts["rag_tool_calls"] += 1
        counts["rag_requirement_met"] = True


def _record_primer_read(counts: dict[str, Any]) -> None:
    counts["primer_read"] = True
    counts["primer_read_tool_calls"] = counts.get("primer_read_tool_calls", 0) + 1


def _record_pseudo_tool_invocations(counts: dict[str, Any], text: str) -> None:
    pseudo_tool_counts = counts.setdefault("pseudo_tool_counts", {})
    for tool_name in _extract_pseudo_tool_invocations(text):
        pseudo_tool_counts[tool_name] = pseudo_tool_counts.get(tool_name, 0) + 1
        counts["pseudo_tool_calls"] = counts.get("pseudo_tool_calls", 0) + 1
        if _is_rag_tool(tool_name):
            counts["rag_pseudo_invocations"] = (
                counts.get("rag_pseudo_invocations", 0) + 1
            )


def _has_non_rag_pseudo_tool(counts: dict[str, Any]) -> bool:
    return any(
        not _is_rag_tool(str(tool_name))
        for tool_name in counts.get("pseudo_tool_counts", {})
    )


def classify_final_status(
    *,
    process_status: str,
    requires_rag: bool,
    counts: dict[str, Any],
) -> str:
    if process_status == "success" and _has_non_rag_pseudo_tool(counts):
        return "failed_pseudo_tool"
    if process_status == "success" and requires_rag and not bool(counts["rag_requirement_met"]):
        if counts.get("rag_mcp_unavailable") or counts.get("rag_pseudo_invocations"):
            return "failed_rag_unavailable"
        return "failed_no_rag"
    return process_status


def pseudo_tool_retry_prompt(previous_status: str, counts: dict[str, Any]) -> str:
    pseudo_counts = counts.get("pseudo_tool_counts", {})
    pseudo_summary = ", ".join(
        f"{name} x{count}" for name, count in sorted(pseudo_counts.items())
    ) or "unknown pseudo tool"
    return (
        "\n\n--- RETRY AFTER NON-EXECUTED TOOL OUTPUT ---\n"
        f"The previous attempt ended as {previous_status}. It printed pseudo tool "
        f"invocations ({pseudo_summary}) as text. Those blocks did not execute and "
        "did not create files or call RAG. Retry from the beginning now.\n"
        "Use only real runtime tool calls. Do not print <invoke>, <parameter>, "
        "minimax:tool_call, or similar wrappers. If you need to write XML files, "
        "call the actual Write tool when it is available, otherwise use actual Edit "
        "or Bash tool calls. If RAG is required, call the actual geos-rag MCP tools.\n"
        "--- END RETRY NOTICE ---"
    )


def archive_native_attempt_outputs(result_dir: Path, attempt: int) -> None:
    archive_dir = result_dir / f"attempt_{attempt}"
    archive_dir.mkdir(exist_ok=True)
    for filename in (
        "status.json",
        "tool_calls.json",
        "events.jsonl",
        "acpx_output.json",
        "stdout.txt",
        "stderr.txt",
        "exit_code.txt",
    ):
        path = result_dir / filename
        if path.exists():
            path.replace(archive_dir / filename)


def _record_mcp_statuses(counts: dict[str, Any], statuses: dict[str, str]) -> None:
    if not statuses:
        return
    current = counts.setdefault("mcp_server_statuses", {})
    current.update(statuses)
    geos_status = statuses.get("geos-rag")
    if geos_status and geos_status.lower() not in {"running", "ready", "connected", "available"}:
        counts["rag_mcp_unavailable"] = True


def analyze_event_stream_text(text: str) -> dict[str, Any]:
    counts = _new_tool_counts()
    stdout_tail: list[str] = []
    latest_agent_response = ""

    for line in text.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            if line.strip():
                stdout_tail.append(line.strip())
            continue

        _record_mcp_statuses(counts, _extract_mcp_server_statuses(record))
        for tool_call in _extract_tool_calls(record):
            _record_tool_call(counts, str(tool_call["name"]))
            if _is_geos_primer_read(tool_call):
                _record_primer_read(counts)
        for fragment in _extract_text_fragments(record):
            fragment_text = fragment["text"]
            stdout_tail.append(fragment_text)
            _record_pseudo_tool_invocations(counts, fragment_text)
            if fragment.get("role") == "assistant":
                latest_agent_response = fragment_text

    return {
        "counts": counts,
        "latest_stdout": stdout_tail[-40:],
        "latest_agent_response": latest_agent_response,
    }


def write_claude_mcp_config(
    *,
    result_dir: Path,
    blocked_xml_filenames: list[str],
    blocked_rst_relpaths: list[str],
) -> Path:
    """Write the explicit MCP config Claude Code uses inside the container.

    Claude Code loads repo3 plugin skills via --plugin-dir in this eval path, but
    the plugin manifest's mcpServers block is not reliably activated in --bare
    mode.  Passing an explicit --mcp-config keeps the RAG tools available without
    storing API secrets in the workspace file; secrets are supplied through the
    docker process environment.
    """
    mcp_config_path = result_dir / CONTAINER_MCP_CONFIG_PATH.name
    _safe_write_json(
        mcp_config_path,
        {
            "mcpServers": {
                "geos-rag": {
                    "type": "stdio",
                    "command": "uv",
                    "args": [
                        "run",
                        "--script",
                        str(CONTAINER_PLUGIN_DIR / "scripts" / "geos_rag_mcp.py"),
                    ],
                    "env": {
                        "CLAUDE_PLUGIN_ROOT": str(CONTAINER_PLUGIN_DIR),
                        "GEOS_VECTOR_DB_DIR": str(CONTAINER_VECTOR_DB_DIR),
                        "EXCLUDED_GT_XML_FILENAMES": json.dumps(blocked_xml_filenames),
                        "EXCLUDED_RST_PATHS": json.dumps(blocked_rst_relpaths),
                    },
                },
            },
        },
    )
    return mcp_config_path


def build_claude_native_mcp_smoke_command(
    *,
    result_dir: Path,
    plugin_dir: Path,
    vector_db_dir: Path,
) -> list[str]:
    return [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{result_dir}:/workspace:rw",
        "-v", f"{plugin_dir}:/plugins/repo3:ro",
        "-v", f"{vector_db_dir}:{CONTAINER_VECTOR_DB_DIR}:rw",
        "-e", "HOME=/workspace/.claude_home",
        "-e", "UV_CACHE_DIR=/workspace/.uv_cache",
        "-e", "CLAUDE_PLUGIN_ROOT=/plugins/repo3",
        "-e", f"GEOS_VECTOR_DB_DIR={CONTAINER_VECTOR_DB_DIR}",
        DOCKER_IMAGE,
        "uv",
        "run",
        "--script",
        str(CONTAINER_PLUGIN_DIR / "scripts" / "geos_rag_mcp.py"),
        "--smoke",
    ]


def preflight_claude_native_mcp(
    *,
    result_dir: Path,
    plugin_dir: Path,
    vector_db_dir: Path,
    timeout: int = 180,
) -> dict[str, Any]:
    """Warm the uv script env and prove the repo3 MCP server can open its DB."""
    cmd = build_claude_native_mcp_smoke_command(
        result_dir=result_dir,
        plugin_dir=plugin_dir,
        vector_db_dir=vector_db_dir,
    )
    started = time.time()
    completed = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    result = {
        "command": cmd,
        "exit_code": completed.returncode,
        "elapsed_seconds": round(time.time() - started, 1),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "updated": datetime.now().isoformat(),
    }
    (result_dir / "mcp_preflight.json").write_text(json.dumps(result, indent=2))
    if completed.returncode != 0:
        detail = "\n".join(
            part.strip()
            for part in (completed.stdout, completed.stderr)
            if part.strip()
        )
        raise RuntimeError(
            "repo3 GEOS RAG MCP preflight failed before launching Claude. "
            "Rebuild the geos-eval image if uv is missing, then rerun. "
            f"Details: {detail or 'no output'}"
        )
    return result


def build_claude_native_command(
    *,
    filtered_geos: Path,
    result_dir: Path,
    plugin_dir: Path,
    vector_db_dir: Path,
    model: str,
    prompt: str,
) -> list[str]:
    return [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{filtered_geos}:/geos_lib:ro",
        "-v", f"{result_dir}:/workspace:rw",
        "-v", f"{plugin_dir}:/plugins/repo3:ro",
        "-v", f"{vector_db_dir}:{CONTAINER_VECTOR_DB_DIR}:rw",
        "-e", "HOME=/workspace/.claude_home",
        "-e", "XDG_CONFIG_HOME=/workspace/.claude_home/.config",
        "-e", "UV_CACHE_DIR=/workspace/.uv_cache",
        "-e", "ANTHROPIC_BASE_URL",
        "-e", "ANTHROPIC_AUTH_TOKEN",
        "-e", "ANTHROPIC_API_KEY",
        "-e", "OPENROUTER_API_KEY",
        "-e", "OPENAI_API_KEY",
        "-e", "GEOS_VECTOR_DB_DIR",
        "-e", "EXCLUDED_GT_XML_FILENAMES",
        "-e", "EXCLUDED_RST_PATHS",
        DOCKER_IMAGE,
        "claude",
        "-p",
        "--bare",
        "--verbose",
        "--model", model,
        "--tools", NATIVE_CLAUDE_TOOLS,
        "--plugin-dir", str(CONTAINER_PLUGIN_DIR),
        f"--mcp-config={CONTAINER_MCP_CONFIG_PATH}",
        "--strict-mcp-config",
        "--output-format", "stream-json",
        "--permission-mode", "bypassPermissions",
        prompt,
    ]


def build_claude_native_env(
    *,
    blocked_xml_filenames: list[str],
    blocked_rst_relpaths: list[str],
    vector_db_dir: Path,
) -> dict[str, str]:
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = os.environ.get(
        "ANTHROPIC_BASE_URL",
        "https://openrouter.ai/api",
    )
    env["GEOS_VECTOR_DB_DIR"] = str(CONTAINER_VECTOR_DB_DIR)
    env["EXCLUDED_GT_XML_FILENAMES"] = json.dumps(blocked_xml_filenames)
    env["EXCLUDED_RST_PATHS"] = json.dumps(blocked_rst_relpaths)

    # The repo3 MCP server uses OPENROUTER_API_KEY for embeddings.  For this
    # eval path, the OpenRouter Claude auth token is a suitable fallback without
    # putting a secret in the docker command line.
    if not env.get("OPENROUTER_API_KEY") and env.get("ANTHROPIC_AUTH_TOKEN"):
        env["OPENROUTER_API_KEY"] = env["ANTHROPIC_AUTH_TOKEN"]

    # Keep the host path available in metadata/debug logs without overriding the
    # container-visible GEOS_VECTOR_DB_DIR used by the MCP server.
    env["HOST_GEOS_VECTOR_DB_DIR"] = str(vector_db_dir)
    return env


def run_claude_native_task(
    *,
    task_name: str,
    agent_key: str,
    run_name: str,
    cmd: list[str],
    docker_env: dict[str, str],
    result_dir: Path,
    timeout: int,
    requires_rag: bool,
) -> dict[str, Any]:
    status_path = result_dir / "status.json"
    tool_counts_path = result_dir / "tool_calls.json"
    events_path = result_dir / "events.jsonl"
    compatibility_output_path = result_dir / "acpx_output.json"
    stdout_text_path = result_dir / "stdout.txt"
    stderr_path = result_dir / "stderr.txt"
    exit_code_path = result_dir / "exit_code.txt"

    counts = _new_tool_counts()
    started = time.time()
    stdout_tail: list[str] = []
    stderr_tail: list[str] = []
    latest_agent_response = ""
    lock = threading.Lock()

    state: dict[str, Any] = {
        "task": task_name,
        "agent": agent_key,
        "run_name": run_name,
        "status": "running",
        "process_status": "running",
        "exit_code": None,
        "started": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "elapsed_seconds": 0.0,
        "latest_stdout": [],
        "latest_agent_response": "",
        "latest_stderr": [],
        **counts,
    }

    def flush_status() -> None:
        with lock:
            state.update(counts)
            state["updated"] = datetime.now().isoformat()
            state["elapsed_seconds"] = round(time.time() - started, 1)
            state["latest_stdout"] = stdout_tail[-40:]
            state["latest_agent_response"] = latest_agent_response
            state["latest_stderr"] = stderr_tail[-40:]
            _safe_write_json(status_path, state)
            _safe_write_json(tool_counts_path, counts)

    flush_status()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=docker_env,
    )
    _register_process(proc)

    def read_stdout() -> None:
        nonlocal latest_agent_response
        assert proc.stdout is not None
        with (
            events_path.open("w", encoding="utf-8") as events_file,
            compatibility_output_path.open("w", encoding="utf-8") as compat_file,
            stdout_text_path.open("w", encoding="utf-8") as stdout_file,
        ):
            for line in proc.stdout:
                events_file.write(line)
                events_file.flush()
                compat_file.write(line)
                compat_file.flush()
                stdout_file.write(line)
                stdout_file.flush()

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    fragments = [{"role": "stdout", "text": line.strip()}] if line.strip() else []
                    tool_calls: list[dict[str, Any]] = []
                    mcp_statuses: dict[str, str] = {}
                else:
                    fragments = _extract_text_fragments(record)
                    tool_calls = _extract_tool_calls(record)
                    mcp_statuses = _extract_mcp_server_statuses(record)

                with lock:
                    _record_mcp_statuses(counts, mcp_statuses)
                    for tool_call in tool_calls:
                        _record_tool_call(counts, str(tool_call["name"]))
                        if _is_geos_primer_read(tool_call):
                            _record_primer_read(counts)
                    for fragment in fragments:
                        text = fragment["text"]
                        stdout_tail.append(text)
                        _record_pseudo_tool_invocations(counts, text)
                        if fragment.get("role") == "assistant":
                            latest_agent_response = text
                    if len(stdout_tail) > 100:
                        del stdout_tail[:-100]
                flush_status()

    def read_stderr() -> None:
        assert proc.stderr is not None
        with stderr_path.open("w", encoding="utf-8") as stderr_file:
            for line in proc.stderr:
                stderr_file.write(line)
                stderr_file.flush()
                text = line.strip()
                if text:
                    with lock:
                        stderr_tail.append(text)
                        if len(stderr_tail) > 100:
                            del stderr_tail[:-100]
                    flush_status()

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    heartbeat_stop = threading.Event()

    def heartbeat_status() -> None:
        while not heartbeat_stop.wait(2.0):
            if proc.poll() is not None:
                break
            flush_status()

    heartbeat_thread = threading.Thread(target=heartbeat_status, daemon=True)
    heartbeat_thread.start()

    try:
        return_code = proc.wait(timeout=timeout)
        if STOP_REQUESTED.is_set() and return_code != 0:
            process_status = "interrupted"
        else:
            process_status = "success" if return_code == 0 else "failed"
    except subprocess.TimeoutExpired:
        proc.kill()
        return_code = None
        process_status = "timeout"
    finally:
        heartbeat_stop.set()
        _unregister_process(proc)
        heartbeat_thread.join(timeout=5)
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)

    rag_requirement_met = bool(counts["rag_requirement_met"])
    status = classify_final_status(
        process_status=process_status,
        requires_rag=requires_rag,
        counts=counts,
    )

    exit_code_path.write_text("timeout" if return_code is None else str(return_code))
    with lock:
        state["status"] = status
        state["process_status"] = process_status
        state["exit_code"] = return_code
        state["rag_requirement_met"] = rag_requirement_met
    flush_status()

    return {
        "task": task_name,
        "agent": agent_key,
        "status": status,
        "process_status": process_status,
        "exit_code": return_code,
        "rag_requirement_met": rag_requirement_met,
        "primer_read": bool(counts.get("primer_read")),
        "primer_read_tool_calls": counts.get("primer_read_tool_calls", 0),
        "total_tool_calls": counts["total_tool_calls"],
        "per_tool_counts": counts["per_tool_counts"],
        "pseudo_tool_calls": counts.get("pseudo_tool_calls", 0),
        "pseudo_tool_counts": counts.get("pseudo_tool_counts", {}),
    }


# ---------------------------------------------------------------------------
# Per-task runner
# ---------------------------------------------------------------------------

def run_task(
    task_name: str,
    agent_key: str,
    agents_context: str,
    experiments_dir: Path,
    run_name: str,
    timeout: int,
    dry_run: bool,
    pseudo_tool_retries: int = 1,
    ground_truth_dir: Path | None = None,
    plugin_dir: Path | None = None,
    vector_db_dir: Path | None = None,
    geos_primer_path: Path | None = None,
    claude_model: str | None = None,
    tmp_geos_parent: Path | None = None,
) -> dict:
    agent = AGENTS[agent_key]
    task_dir = experiments_dir / task_name
    result_dir = agent["results_dir"] / run_name / task_name

    # Ensure workspace subdirs exist on the host before mounting
    (result_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (result_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (result_dir / ".claude_home" / ".config").mkdir(parents=True, exist_ok=True)
    (result_dir / ".uv_cache").mkdir(parents=True, exist_ok=True)

    task_instructions = load_task_instructions(task_dir)
    prompt = build_prompt(agents_context, task_instructions)
    resolved_geos_primer_path = (geos_primer_path or DEFAULT_GEOS_PRIMER_PATH).resolve()
    primer_workspace_path: Path | None = None
    if resolved_geos_primer_path.exists():
        primer_workspace_path = copy_geos_primer(resolved_geos_primer_path, result_dir)
        prompt = prepend_geos_primer_instruction(prompt)

    # Collect blocked GT XML filenames for this experiment
    blocked_xml_filenames: list[str] = []
    if ground_truth_dir is not None:
        gt_experiment_dir = ground_truth_dir / task_name
        blocked_xml_filenames = collect_ground_truth_xml_filenames(gt_experiment_dir)

    # Create a per-task filtered copy of GEOS with blocked files excluded.
    # This is the primary enforcement mechanism for file-read restrictions: the
    # files simply don't exist in the agent's /geos_lib mount. Dry-runs skip the
    # copy and only display the command shape.
    cleanup_filtered_copy = False
    if dry_run:
        filtered_geos = GEOS_LIB_DIR
    else:
        filtered_geos = create_filtered_geos_copy(
            geos_src=GEOS_LIB_DIR,
            blocked_xml_basenames=set(blocked_xml_filenames),
            tmp_parent=tmp_geos_parent or TEMP_GEOS_PARENT,
        )
        cleanup_filtered_copy = True

    runner = agent.get("runner", "acpx")
    if runner == "claude_native":
        plugin_dir = (plugin_dir or DEFAULT_PLUGIN_DIR).resolve()
        vector_db_dir = (vector_db_dir or DEFAULT_VECTOR_DB_DIR).resolve()
        cleanup_vector_db_copy = False
        runtime_vector_db_dir = result_dir / ".vector_db_runtime"
        if not dry_run:
            try:
                runtime_vector_db_dir = create_runtime_vector_db_copy(vector_db_dir, result_dir)
                cleanup_vector_db_copy = True
            except Exception:
                if cleanup_filtered_copy:
                    cleanup_filtered_geos_copy(filtered_geos)
                raise
        blocked_rst_relpaths: list[str] = []
        mcp_config_path = write_claude_mcp_config(
            result_dir=result_dir,
            blocked_xml_filenames=blocked_xml_filenames,
            blocked_rst_relpaths=blocked_rst_relpaths,
        )
        native_model = claude_model or agent.get("model") or DEFAULT_CLAUDE_MODEL
        native_prompt = (
            "Use the repo3-plugin geos-rag skill for this task. "
            "Before writing XML, call at least one of the plugin RAG tools: "
            "search_navigator, search_schema, or search_technical.\n\n"
            f"{prompt}"
        )
        cmd = build_claude_native_command(
            filtered_geos=filtered_geos,
            result_dir=result_dir,
            plugin_dir=plugin_dir,
            vector_db_dir=runtime_vector_db_dir,
            model=native_model,
            prompt=native_prompt,
        )
        docker_env = build_claude_native_env(
            blocked_xml_filenames=blocked_xml_filenames,
            blocked_rst_relpaths=blocked_rst_relpaths,
            vector_db_dir=vector_db_dir,
        )

        if dry_run:
            display = redact_command_for_display(cmd[:-1] + ["<prompt>"])
            print(f"  [DRY RUN] {display}")
            return {"task": task_name, "agent": agent_key, "status": "dry_run"}

        (result_dir / "eval_metadata.json").write_text(
            json.dumps(
                {
                    "task": task_name,
                    "agent": agent_key,
                    "runner": runner,
                    "run_name": run_name,
                    "plugin_dir": str(plugin_dir),
                    "plugin_manifest": str(plugin_dir / ".claude-plugin" / "plugin.json"),
                    "vector_db_dir": str(vector_db_dir),
                    "runtime_vector_db_dir": str(runtime_vector_db_dir),
                    "container_plugin_dir": str(CONTAINER_PLUGIN_DIR),
                    "container_vector_db_dir": str(CONTAINER_VECTOR_DB_DIR),
                    "mcp_config_path": str(mcp_config_path),
                    "container_mcp_config_path": str(CONTAINER_MCP_CONFIG_PATH),
                    "geos_primer_path": str(resolved_geos_primer_path),
                    "primer_workspace_path": str(primer_workspace_path) if primer_workspace_path else None,
                    "container_geos_primer_path": str(CONTAINER_GEOS_PRIMER_PATH),
                    "claude_model": native_model,
                    "anthropic_base_url": docker_env.get("ANTHROPIC_BASE_URL"),
                    "blocked_gt_xml_filenames": blocked_xml_filenames,
                    "blocked_rst_relpaths": blocked_rst_relpaths,
                    "filtered_geos_copy": str(filtered_geos),
                    "requires_rag": bool(agent.get("requires_rag")),
                    "started": datetime.now().isoformat(),
                },
                indent=2,
            )
        )

        try:
            _safe_write_json(
                result_dir / "status.json",
                {
                    "task": task_name,
                    "agent": agent_key,
                    "run_name": run_name,
                    "status": "preflight",
                    "process_status": "preflight",
                    "updated": datetime.now().isoformat(),
                    "blocked_gt_xml_filenames": blocked_xml_filenames,
                    **_new_tool_counts(),
                },
            )
            preflight_claude_native_mcp(
                result_dir=result_dir,
                plugin_dir=plugin_dir,
                vector_db_dir=runtime_vector_db_dir,
            )

            attempt = 0
            current_cmd = cmd
            while True:
                result = run_claude_native_task(
                    task_name=task_name,
                    agent_key=agent_key,
                    run_name=run_name,
                    cmd=current_cmd,
                    docker_env=docker_env,
                    result_dir=result_dir,
                    timeout=timeout,
                    requires_rag=bool(agent.get("requires_rag")),
                )
                retryable_status = result.get("status") in {
                    "failed_pseudo_tool",
                    "failed_rag_unavailable",
                }
                if (
                    not retryable_status
                    or int(result.get("pseudo_tool_calls") or 0) <= 0
                    or attempt >= pseudo_tool_retries
                    or STOP_REQUESTED.is_set()
                ):
                    return result

                attempt += 1
                archive_native_attempt_outputs(result_dir, attempt)
                notice = pseudo_tool_retry_prompt(
                    str(result.get("status")),
                    {
                        "pseudo_tool_counts": result.get("pseudo_tool_counts", {}),
                    },
                )
                retry_prompt = f"{native_prompt}{notice}"
                current_cmd = build_claude_native_command(
                    filtered_geos=filtered_geos,
                    result_dir=result_dir,
                    plugin_dir=plugin_dir,
                    vector_db_dir=runtime_vector_db_dir,
                    model=native_model,
                    prompt=retry_prompt,
                )
                _safe_write_json(
                    result_dir / "status.json",
                    {
                        "task": task_name,
                        "agent": agent_key,
                        "run_name": run_name,
                        "status": "retrying_pseudo_tool",
                        "process_status": "retrying_pseudo_tool",
                        "updated": datetime.now().isoformat(),
                        "retry_attempt": attempt,
                        "previous_status": result.get("status"),
                        "pseudo_tool_counts": result.get("pseudo_tool_counts", {}),
                        "blocked_gt_xml_filenames": blocked_xml_filenames,
                        **_new_tool_counts(),
                    },
                )
        except Exception as exc:
            (result_dir / "exit_code.txt").write_text("error")
            (result_dir / "stderr.txt").write_text(str(exc))
            _safe_write_json(
                result_dir / "status.json",
                {
                    "task": task_name,
                    "agent": agent_key,
                    "run_name": run_name,
                    "status": "error",
                    "process_status": "error",
                    "error": str(exc),
                    "updated": datetime.now().isoformat(),
                },
            )
            return {"task": task_name, "agent": agent_key, "status": "error", "error": str(exc)}
        finally:
            if cleanup_vector_db_copy:
                shutil.rmtree(runtime_vector_db_dir, ignore_errors=True)
            if cleanup_filtered_copy:
                cleanup_filtered_geos_copy(filtered_geos)

    model = agent.get("model")
    api_key = os.environ.get(agent["api_key_env"], "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # For cursor: prepend /model slash command as the most reliable way to set
    # the model within an acpx session (Cursor ACP doesn't advertise models yet).
    if model and agent["acpx_name"] == "cursor":
        prompt = f"/model {model}\n\n{prompt}"

    extra_env: list[str] = []
    if model and agent["acpx_name"] == "cursor":
        extra_env += ["-e", f"CURSOR_MODEL={model}"]

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{filtered_geos}:/geos_lib:ro",
        "-v", f"{result_dir}:/workspace:rw",
        "-e", f"{agent['api_key_env']}={api_key}",
        "-e", f"ANTHROPIC_API_KEY={anthropic_key}",
        *extra_env,
        DOCKER_IMAGE,
        "acpx",
        "--approve-reads",
        "--format", "json",
        "--cwd", "/workspace",
        agent["acpx_name"],
        "exec", prompt,
    ]

    if dry_run:
        display = redact_command_for_display(cmd[:-1] + ["<prompt>"])
        print(f"  [DRY RUN] {display}")
        return {"task": task_name, "agent": agent_key, "status": "dry_run"}

    started_time = time.time()
    started_iso = datetime.now().isoformat()

    def write_acpx_status(
        status: str,
        *,
        process_status: str | None = None,
        exit_code: int | None = None,
        stdout: str = "",
        stderr: str = "",
        error: str | None = None,
    ) -> None:
        analysis = analyze_event_stream_text(stdout) if stdout else {
            "counts": _new_tool_counts(),
            "latest_stdout": [],
            "latest_agent_response": "",
        }
        payload: dict[str, Any] = {
            "task": task_name,
            "agent": agent_key,
            "run_name": run_name,
            "status": status,
            "process_status": process_status or status,
            "exit_code": exit_code,
            "started": started_iso,
            "updated": datetime.now().isoformat(),
            "elapsed_seconds": round(time.time() - started_time, 1),
            "latest_stdout": analysis["latest_stdout"] or stdout.splitlines()[-40:],
            "latest_agent_response": analysis["latest_agent_response"],
            "latest_stderr": stderr.splitlines()[-40:],
            **analysis["counts"],
        }
        if error:
            payload["error"] = error
        _safe_write_json(result_dir / "status.json", payload)

    write_acpx_status("running", process_status="running")
    heartbeat_stop = threading.Event()
    proc_holder: dict[str, subprocess.Popen[str] | None] = {"proc": None}

    def heartbeat_acpx_status() -> None:
        while not heartbeat_stop.wait(2.0):
            proc = proc_holder["proc"]
            if proc is None:
                continue
            if proc.poll() is not None:
                break
            write_acpx_status("running", process_status="running")

    heartbeat_thread = threading.Thread(target=heartbeat_acpx_status, daemon=True)
    heartbeat_thread.start()

    # Write a metadata file so the run config is auditable
    (result_dir / "eval_metadata.json").write_text(
        json.dumps(
            {
                "task": task_name,
                "agent": agent_key,
                "run_name": run_name,
                "blocked_gt_xml_filenames": blocked_xml_filenames,
                "filtered_geos_copy": str(filtered_geos),
                "geos_primer_path": str(resolved_geos_primer_path),
                "primer_workspace_path": str(primer_workspace_path) if primer_workspace_path else None,
                "container_geos_primer_path": str(CONTAINER_GEOS_PRIMER_PATH),
                "started": started_iso,
            },
            indent=2,
        )
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        proc_holder["proc"] = proc
        _register_process(proc)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        finally:
            _unregister_process(proc)
        if STOP_REQUESTED.is_set() and proc.returncode != 0:
            status = "interrupted"
        else:
            status = "success" if proc.returncode == 0 else "failed"
        if status == "success":
            status = classify_final_status(
                process_status=status,
                requires_rag=False,
                counts=analyze_event_stream_text(stdout)["counts"],
            )
        (result_dir / "acpx_output.json").write_text(stdout)
        (result_dir / "stderr.txt").write_text(stderr)
        (result_dir / "exit_code.txt").write_text(str(proc.returncode))
        write_acpx_status(
            status,
            process_status=status,
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
        )

        return {
            "task": task_name,
            "agent": agent_key,
            "status": status,
            "exit_code": proc.returncode,
        }

    except KeyboardInterrupt:
        stop_active_processes()
        (result_dir / "exit_code.txt").write_text("interrupted")
        (result_dir / "stderr.txt").write_text("Interrupted by user")
        write_acpx_status(
            "interrupted",
            process_status="interrupted",
            stderr="Interrupted by user",
        )
        return {"task": task_name, "agent": agent_key, "status": "interrupted"}

    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        _unregister_process(proc)
        (result_dir / "acpx_output.json").write_text(stdout)
        (result_dir / "stderr.txt").write_text(stderr)
        (result_dir / "exit_code.txt").write_text("timeout")
        write_acpx_status(
            "timeout",
            process_status="timeout",
            stdout=stdout,
            stderr=stderr,
        )
        return {"task": task_name, "agent": agent_key, "status": "timeout"}

    except Exception as exc:
        (result_dir / "exit_code.txt").write_text("error")
        (result_dir / "stderr.txt").write_text(str(exc))
        write_acpx_status(
            "error",
            process_status="error",
            stderr=str(exc),
            error=str(exc),
        )
        return {"task": task_name, "agent": agent_key, "status": "error", "error": str(exc)}

    finally:
        heartbeat_stop.set()
        heartbeat_thread.join(timeout=5)
        if cleanup_filtered_copy:
            cleanup_filtered_geos_copy(filtered_geos)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

class C:
    GREEN   = "\033[92m"
    WARNING = "\033[93m"
    FAIL    = "\033[91m"
    CYAN    = "\033[96m"
    BOLD    = "\033[1m"
    HEADER  = "\033[95m"
    ENDC    = "\033[0m"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def collect_dashboard_snapshot(
    run_name: str,
    agent_keys: list[str],
    task_names: list[str] | None = None,
    blocked_gt_by_task: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    expected_task_names = set(task_names or [])
    blocked_gt_by_task = blocked_gt_by_task or {}
    for agent_key in agent_keys:
        root = AGENTS[agent_key]["results_dir"] / run_name
        discovered_task_names = set(expected_task_names)
        if root.exists():
            discovered_task_names.update(path.name for path in root.iterdir() if path.is_dir())
        for task_name in sorted(discovered_task_names):
            task_dir = root / task_name
            metadata = _read_json(task_dir / "eval_metadata.json") or {}
            default_status = {
                "task": task_name,
                "agent": agent_key,
                "run_name": run_name,
                "status": "pending",
                "process_status": "pending",
                "latest_stdout": [],
                "latest_agent_response": "",
                "latest_stderr": [],
                "blocked_gt_xml_filenames": metadata.get(
                    "blocked_gt_xml_filenames",
                    blocked_gt_by_task.get(task_name, []),
                ),
                **_new_tool_counts(),
            }
            status = {**default_status, **(_read_json(task_dir / "status.json") or {})}
            status["task_dir"] = str(task_dir)
            if "blocked_gt_xml_filenames" not in status:
                status["blocked_gt_xml_filenames"] = default_status["blocked_gt_xml_filenames"]
            tasks.append(status)
    tasks.sort(key=lambda item: (str(item.get("agent", "")), str(item.get("task", ""))))
    return {
        "run_name": run_name,
        "updated": datetime.now().isoformat(),
        "tasks": tasks,
    }


def _conversation_label(record: dict[str, Any]) -> str:
    record_type = str(record.get("type") or "event")
    if record_type == "system":
        subtype = record.get("subtype")
        return f"system:{subtype}" if subtype else "system"
    message = record.get("message")
    if isinstance(message, dict) and message.get("role"):
        return str(message["role"])
    return record_type


def _conversation_text(record: dict[str, Any]) -> str:
    if record.get("type") == "system":
        summary = {
            key: record.get(key)
            for key in ("subtype", "cwd", "session_id", "model", "tools", "mcp_servers", "plugins")
            if key in record
        }
        return json.dumps(summary, indent=2, sort_keys=True)

    message = record.get("message")
    if not isinstance(message, dict):
        return json.dumps(record, indent=2, sort_keys=True)

    parts: list[str] = []
    content = message.get("content")
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                parts.append(str(item))
                continue
            item_type = item.get("type")
            if item_type == "text":
                parts.append(str(item.get("text", "")))
            elif item_type == "thinking":
                parts.append("[thinking]\n" + str(item.get("thinking", "")))
            elif item_type == "redacted_thinking":
                parts.append("[redacted thinking]")
            elif item_type == "tool_use":
                tool_name = item.get("name", "tool")
                tool_input = item.get("input", {})
                parts.append(
                    f"[tool use] {tool_name}\n"
                    f"{json.dumps(tool_input, indent=2, sort_keys=True)}"
                )
            elif item_type == "tool_result":
                result = item.get("content", "")
                parts.append(f"[tool result] {item.get('tool_use_id', '')}\n{result}")
            else:
                parts.append(json.dumps(item, indent=2, sort_keys=True))

    if parts:
        return "\n\n".join(part for part in parts if part)
    return json.dumps(message, indent=2, sort_keys=True)


def collect_conversation_log(
    *,
    run_name: str,
    agent_keys: list[str],
    agent_key: str,
    task_name: str,
) -> dict[str, Any]:
    if agent_key not in agent_keys:
        return {"error": f"agent not in dashboard scope: {agent_key}", "entries": []}

    task_dir = AGENTS[agent_key]["results_dir"] / run_name / task_name
    try:
        task_dir.relative_to(AGENTS[agent_key]["results_dir"] / run_name)
    except ValueError:
        return {"error": "invalid task path", "entries": []}

    status = _read_json(task_dir / "status.json") or {}
    metadata = _read_json(task_dir / "eval_metadata.json") or {}
    blocked_gt_xml_filenames = (
        status.get("blocked_gt_xml_filenames")
        or metadata.get("blocked_gt_xml_filenames")
        or []
    )

    entries: list[dict[str, str]] = []
    events_path = task_dir / "events.jsonl"
    if events_path.exists():
        with events_path.open("r", encoding="utf-8", errors="replace") as events_file:
            for index, line in enumerate(events_file, 1):
                line = line.rstrip("\n")
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    entries.append({"label": f"stdout:{index}", "text": line})
                    continue
                entries.append(
                    {
                        "label": _conversation_label(record),
                        "text": _conversation_text(record),
                    }
                )
    else:
        for label, filename in (("stdout", "stdout.txt"), ("stderr", "stderr.txt")):
            path = task_dir / filename
            if path.exists():
                entries.append(
                    {
                        "label": label,
                        "text": path.read_text(encoding="utf-8", errors="replace"),
                    }
                )

    return {
        "task": task_name,
        "agent": agent_key,
        "task_dir": str(task_dir),
        "blocked_gt_xml_filenames": blocked_gt_xml_filenames,
        "entries": entries,
    }


def dashboard_html() -> bytes:
    return b"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GEOS Claude Eval Dashboard</title>
  <style>
    :root {
      --paper: #f6f4ee;
      --paper-2: #eae5d5;
      --ink: #161616;
      --muted: #5b5b55;
      --rule: #c6c0b0;
      --heavy: #161616;
      --green: #0b7e7e;
      --amber: #c08b2d;
      --red: #a83232;
      --blue: #2d5ea8;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      min-height: 100%;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .mono {
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .masthead {
      padding: 22px 28px 16px;
      border-bottom: 2px solid var(--heavy);
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
    }
    .masthead h1 {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 30px;
      line-height: 1;
      letter-spacing: -0.01em;
      font-weight: 600;
    }
    .masthead h1 em {
      font-style: italic;
      color: var(--green);
      font-weight: 400;
    }
    .runline {
      margin-top: 8px;
      color: var(--muted);
      font: 500 11px/1.4 "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .live {
      color: var(--green);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .live i {
      width: 6px;
      height: 6px;
      background: var(--green);
      border-radius: 50%;
      animation: blink 1.2s infinite;
    }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: .25; } }
    @keyframes slide { 0% { transform: translateX(-100%); } 100% { transform: translateX(260%); } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .25; } }
    .agent-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      border-bottom: 1px solid var(--heavy);
    }
    .agent-card {
      padding: 16px 22px;
      border-right: 1px solid var(--rule);
      min-height: 142px;
    }
    .agent-card:last-child { border-right: none; }
    .agent-card .k {
      color: var(--muted);
      font: 500 10px/1 "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    .agent-card .name {
      font: 600 18px/1.15 "JetBrains Mono", ui-monospace, monospace;
      overflow-wrap: anywhere;
    }
    .agent-card .v {
      margin-top: 14px;
      font: 600 28px/1 "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: -0.02em;
    }
    .agent-card .sub {
      margin-top: 8px;
      color: var(--muted);
      font: 400 12px/1.35 "JetBrains Mono", ui-monospace, monospace;
    }
    .barline {
      display: flex;
      height: 6px;
      margin-top: 12px;
      background: #ded8c6;
      overflow: hidden;
    }
    .barline i { display: block; height: 100%; }
    .g { background: var(--green); }
    .a { background: var(--amber); }
    .r { background: var(--red); }
    .b { background: var(--blue); }
    .controls {
      padding: 10px 22px;
      border-bottom: 1px solid var(--rule);
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      font: 500 11px/1 "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .seg {
      display: flex;
      border: 1px solid var(--heavy);
      max-width: 100%;
      overflow-x: auto;
    }
    .seg button {
      background: transparent;
      border: none;
      border-right: 1px solid var(--rule);
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      padding: 7px 11px;
      white-space: nowrap;
    }
    .seg button:last-child { border-right: none; }
    .seg button.on {
      background: var(--heavy);
      color: var(--paper);
    }
    .seg button .ct { color: var(--green); margin-left: 6px; }
    input, select {
      background: var(--paper-2);
      border: 1px solid var(--rule);
      color: var(--ink);
      font: inherit;
      padding: 7px 10px;
      min-height: 31px;
    }
    #search { flex: 1; min-width: 220px; max-width: 360px; }
    .table-wrap { overflow: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
      font: 400 12px/1.4 "JetBrains Mono", ui-monospace, monospace;
    }
    thead th {
      background: var(--paper-2);
      border-bottom: 1px solid var(--heavy);
      border-right: 1px solid var(--rule);
      color: var(--muted);
      font-size: 10px;
      font-weight: 500;
      letter-spacing: 0.08em;
      padding: 10px 14px;
      position: sticky;
      text-align: left;
      text-transform: uppercase;
      top: 0;
      z-index: 3;
    }
    thead th:last-child { border-right: none; }
    tbody td {
      border-bottom: 1px dotted var(--rule);
      padding: 10px 14px;
      vertical-align: middle;
    }
    tbody tr:hover { background: #ece7d7; }
    .rank { color: #8f897a; width: 34px; }
    .task-name { font-weight: 600; color: var(--ink); }
    .task-dir {
      color: var(--muted);
      font-size: 10px;
      margin-top: 3px;
      max-width: 440px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .blocked-gt {
      color: var(--red);
      font-size: 10px;
      font-weight: 600;
      margin-top: 4px;
      max-width: 440px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .muted { color: var(--muted); }
    .stat {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      white-space: nowrap;
    }
    .stat .mark {
      width: 10px;
      height: 10px;
      display: inline-block;
      background: var(--rule);
    }
    .stat.ok { color: var(--green); }
    .stat.run { color: var(--amber); }
    .stat.err, .stat.nrg { color: var(--red); }
    .stat.pnd { color: var(--muted); }
    .stat.ok .mark { background: var(--green); }
    .stat.run .mark { background: var(--amber); animation: pulse 1.4s infinite; }
    .stat.err .mark, .stat.nrg .mark { background: var(--red); }
    .pbar {
      width: 96px;
      height: 4px;
      background: #d8d2c0;
      display: inline-block;
      overflow: hidden;
      position: relative;
      margin-top: 5px;
    }
    .pbar i {
      position: absolute;
      height: 100%;
      width: 40%;
      background: var(--amber);
      animation: slide 1.8s ease-in-out infinite;
    }
    .ragrow {
      display: inline-flex;
      gap: 2px;
      vertical-align: -1px;
    }
    .ragrow s {
      width: 16px;
      height: 10px;
      background: #d8d2c0;
      display: inline-block;
      text-decoration: none;
    }
    .ragrow s.ok { background: var(--green); }
    .ragrow s.part { background: linear-gradient(90deg, var(--green) 50%, #d8d2c0 50%); }
    .tools {
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
      max-width: 260px;
    }
    .tool {
      background: var(--paper-2);
      border: 1px solid var(--rule);
      padding: 2px 6px;
      color: var(--ink);
      white-space: nowrap;
    }
    .tool b {
      color: var(--blue);
      margin-left: 4px;
      font-weight: 600;
    }
    .latest {
      color: var(--muted);
      display: -webkit-box;
      font-size: 10px;
      line-height: 1.35;
      max-height: 5.4em;
      max-width: 520px;
      overflow: hidden;
      white-space: pre-wrap;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 4;
    }
    .latest.err { color: var(--red); }
    .log-btn {
      background: var(--heavy);
      color: var(--paper);
      border: 1px solid var(--heavy);
      border-radius: 2px;
      cursor: pointer;
      font: 600 10px/1 "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: 0.08em;
      padding: 7px 9px;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .log-btn.secondary {
      background: transparent;
      color: var(--ink);
    }
    .empty {
      padding: 40px;
      text-align: center;
      color: var(--muted);
      font: 500 12px/1.4 "JetBrains Mono", ui-monospace, monospace;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .modal {
      position: fixed;
      inset: 0;
      background: rgba(17, 17, 17, 0.62);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 28px;
      z-index: 100;
    }
    .modal.open { display: flex; }
    .modal-card {
      width: min(1120px, 96vw);
      height: min(760px, 90vh);
      background: var(--paper);
      border: 2px solid var(--heavy);
      box-shadow: 0 20px 80px rgba(0,0,0,.35);
      display: flex;
      flex-direction: column;
    }
    .modal-head {
      padding: 14px 18px;
      border-bottom: 1px solid var(--heavy);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
    }
    .modal-title {
      margin: 0;
      font: 600 18px/1.2 Georgia, "Times New Roman", serif;
    }
    .modal-meta {
      margin-top: 5px;
      color: var(--muted);
      font: 500 11px/1.4 "JetBrains Mono", ui-monospace, monospace;
      overflow-wrap: anywhere;
    }
    .modal-actions { display: flex; gap: 8px; }
    .conversation {
      flex: 1;
      overflow: auto;
      padding: 14px 18px 20px;
      background: #fbfaf5;
    }
    .entry {
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 12px;
      border-bottom: 1px dotted var(--rule);
      padding: 10px 0;
    }
    .entry-label {
      color: var(--muted);
      font: 600 10px/1.4 "JetBrains Mono", ui-monospace, monospace;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      overflow-wrap: anywhere;
    }
    .entry-text {
      margin: 0;
      white-space: pre-wrap;
      color: var(--ink);
      font: 400 12px/1.55 "JetBrains Mono", ui-monospace, monospace;
      overflow-wrap: anywhere;
    }
    @media (max-width: 900px) {
      .masthead { align-items: flex-start; }
      .agent-grid { grid-template-columns: 1fr; }
      .agent-card { border-right: none; border-bottom: 1px solid var(--rule); }
      .entry { grid-template-columns: 1fr; }
      .modal { padding: 10px; }
    }
  </style>
</head>
<body>
  <header class="masthead">
    <div>
      <h1>GEOS Eval <em>Lattice</em></h1>
      <div class="runline">
        <span id="run-name">Run</span>
        <span> | </span>
        <span class="live"><i></i>live | 2s refresh</span>
      </div>
    </div>
    <div class="runline" id="updated-at">Updated --</div>
  </header>

  <section class="agent-grid" id="agent-grid"></section>

  <section class="controls">
    <div class="seg" id="status-filters"></div>
    <input id="search" placeholder="filter agent / task / dir">
    <select id="agent-filter" aria-label="Agent filter"></select>
    <select id="sort-mode" aria-label="Sort">
      <option value="elapsed">elapsed desc</option>
      <option value="status">status</option>
      <option value="agent">agent</option>
      <option value="primer">primer</option>
      <option value="rag">rag calls</option>
      <option value="tools">tool calls</option>
    </select>
  </section>

  <main class="table-wrap">
    <table aria-label="GEOS eval tasks">
      <thead>
        <tr>
          <th>#</th>
          <th>Agent</th>
          <th>Task</th>
          <th>Status</th>
          <th>Elapsed</th>
          <th>Primer</th>
          <th>Nav</th>
          <th>Sch</th>
          <th>Tech</th>
          <th>Tools</th>
          <th>Latest</th>
          <th>Conversation</th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
  </main>

  <div class="modal" id="log-modal" role="dialog" aria-modal="true" aria-labelledby="log-title">
    <div class="modal-card">
      <div class="modal-head">
        <div>
          <h2 class="modal-title" id="log-title">Conversation Log</h2>
          <div class="modal-meta" id="log-meta"></div>
        </div>
        <div class="modal-actions">
          <button class="log-btn secondary" id="copy-log">Copy</button>
          <button class="log-btn" id="close-log">Close</button>
        </div>
      </div>
      <div class="conversation" id="conversation"></div>
    </div>
  </div>

  <script>
    let currentData = { run_name: "", updated: "", tasks: [] };
    let selectedStatus = "all";
    let selectedAgent = "all";
    let searchTerm = "";
    let sortMode = "elapsed";
    let lastConversationText = "";

    function cls(status) {
      return String(status || "").replace(/[^a-zA-Z0-9_-]/g, "_");
    }
    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }
    function lines(value) {
      if (Array.isArray(value)) return value.slice(-3).join(" ");
      return value || "";
    }
    function latestExcerpt(value, max = 520) {
      const text = String(value || "").replace(/\\r/g, "").trim();
      if (text.length <= max) return text;
      const head = text.slice(0, Math.floor(max * 0.48)).trimEnd();
      const tail = text.slice(text.length - Math.floor(max * 0.42)).trimStart();
      return `${head}\n...\n${tail}`;
    }
    function statusGroup(status) {
      const s = String(status || "pending");
      if (s === "success") return "ok";
      if (s === "running") return "run";
      if (s === "preflight") return "run";
      if (s === "retrying_pseudo_tool") return "run";
      if (s === "failed_no_rag") return "nrg";
      if (s === "failed_rag_unavailable") return "nrg";
      if (s === "failed_pseudo_tool") return "nrg";
      if (s === "pending") return "pnd";
      return "err";
    }
    function ragCount(task, name) {
      const counts = task.rag_tool_counts || {};
      return Number(counts[name] || 0);
    }
    function ragCell(count) {
      const state = count > 0 ? "ok" : "";
      return `<span class="ragrow"><s class="${state}"></s></span> ${esc(count)}`;
    }
    function blockedGtFiles(task) {
      const files = task.blocked_gt_xml_filenames;
      return Array.isArray(files) ? files : [];
    }
    function blockedGtSummary(task, max = 3) {
      const files = blockedGtFiles(task);
      if (!files.length) return "blocked GT: none";
      const shown = files.slice(0, max).join(", ");
      const extra = files.length > max ? ` +${files.length - max} more` : "";
      return `blocked GT: ${shown}${extra}`;
    }
    function primerCell(task) {
      const read = Boolean(task.primer_read);
      const count = Number(task.primer_read_tool_calls || 0);
      return `<span class="ragrow"><s class="${read ? "ok" : ""}"></s></span> ${read ? `read ${esc(count)}` : "no"}`;
    }
    function fmtElapsed(value) {
      if (value === undefined || value === null || value === "") return "--";
      const n = Number(value);
      if (!Number.isFinite(n)) return esc(value);
      if (n >= 3600) return `${(n / 3600).toFixed(1)}h`;
      if (n >= 60) return `${Math.floor(n / 60)}m ${Math.round(n % 60)}s`;
      return `${n.toFixed(1)}s`;
    }
    function topTools(task, limit = 3) {
      const actual = Object.entries(task.per_tool_counts || {});
      const pseudo = Object.entries(task.pseudo_tool_counts || {})
        .map(([name, count]) => [`pseudo:${name}`, count]);
      return actual.concat(pseudo)
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit)
        .map(([name, count]) => `<span class="tool">${esc(name)}<b>${esc(count)}</b></span>`)
        .join("");
    }
    function agentMetrics(tasks) {
      const byAgent = new Map();
      for (const task of tasks) {
        const agent = task.agent || "unknown";
        if (!byAgent.has(agent)) {
          byAgent.set(agent, {
            agent,
            total: 0,
            success: 0,
            running: 0,
            failed: 0,
            noRag: 0,
            ragUnavailable: 0,
            pseudoTool: 0,
            pending: 0,
            ragMet: 0,
            primerRead: 0,
            tools: 0,
            nav: 0,
            sch: 0,
            tech: 0,
          });
        }
        const m = byAgent.get(agent);
        m.total += 1;
        const status = task.status || "pending";
        if (status === "success") m.success += 1;
        else if (status === "running") m.running += 1;
        else if (status === "preflight") m.running += 1;
        else if (status === "retrying_pseudo_tool") m.running += 1;
        else if (status === "failed_no_rag") m.noRag += 1;
        else if (status === "failed_rag_unavailable") m.ragUnavailable += 1;
        else if (status === "failed_pseudo_tool") m.pseudoTool += 1;
        else if (status === "pending") m.pending += 1;
        else m.failed += 1;
        if (task.rag_requirement_met) m.ragMet += 1;
        if (task.primer_read) m.primerRead += 1;
        m.tools += Number(task.total_tool_calls || 0) + Number(task.pseudo_tool_calls || 0);
        m.nav += ragCount(task, "search_navigator");
        m.sch += ragCount(task, "search_schema");
        m.tech += ragCount(task, "search_technical");
      }
      return Array.from(byAgent.values()).sort((a, b) => a.agent.localeCompare(b.agent));
    }
    function renderAgentCards(tasks) {
      const cards = agentMetrics(tasks);
      document.getElementById("agent-grid").innerHTML = cards.map(m => {
        const denom = Math.max(m.total, 1);
        const health = Math.round((m.success / denom) * 100);
        const ragRate = Math.round((m.ragMet / denom) * 100);
        const primerRate = Math.round((m.primerRead / denom) * 100);
        return `<article class="agent-card">
          <div class="k">Agent</div>
          <div class="name">${esc(m.agent)}</div>
          <div class="v">${esc(m.success)} / ${esc(m.total)}</div>
          <div class="sub">success ${esc(health)}% | running ${esc(m.running)} | error ${esc(m.failed)} | no_rag ${esc(m.noRag)} | rag_down ${esc(m.ragUnavailable)} | pseudo ${esc(m.pseudoTool)} | pending ${esc(m.pending)}</div>
          <div class="barline" aria-hidden="true">
            <i class="g" style="width:${(m.success / denom) * 100}%"></i>
            <i class="a" style="width:${(m.running / denom) * 100}%"></i>
            <i class="r" style="width:${((m.failed + m.noRag + m.ragUnavailable + m.pseudoTool) / denom) * 100}%"></i>
            <i class="b" style="width:${(m.pending / denom) * 100}%"></i>
          </div>
          <div class="sub">Primer ${esc(m.primerRead)} / ${esc(m.total)} (${esc(primerRate)}%) | RAG ${esc(ragRate)}% | nav ${esc(m.nav)} | sch ${esc(m.sch)} | tech ${esc(m.tech)} | tools ${esc(m.tools)}</div>
        </article>`;
      }).join("") || `<div class="empty">No agent metrics yet</div>`;
    }
    function renderFilters(tasks) {
      const statuses = ["all", "preflight", "retrying_pseudo_tool", "running", "success", "failed_pseudo_tool", "failed_rag_unavailable", "failed_no_rag", "failed", "error", "timeout", "pending"];
      document.getElementById("status-filters").innerHTML = statuses.map(status => {
        const on = selectedStatus === status ? "on" : "";
        return `<button class="${on}" data-status="${esc(status)}">${esc(status)}</button>`;
      }).join("");
      document.querySelectorAll("#status-filters button").forEach(button => {
        button.addEventListener("click", () => {
          selectedStatus = button.dataset.status;
          render();
        });
      });

      const agents = ["all", ...new Set(tasks.map(task => task.agent).filter(Boolean).sort())];
      const agentFilter = document.getElementById("agent-filter");
      const previous = selectedAgent;
      agentFilter.innerHTML = agents.map(agent => `<option value="${esc(agent)}">${esc(agent)}</option>`).join("");
      selectedAgent = agents.includes(previous) ? previous : "all";
      agentFilter.value = selectedAgent;
    }
    function filteredTasks() {
      let tasks = [...(currentData.tasks || [])];
      if (selectedStatus !== "all") tasks = tasks.filter(task => (task.status || "pending") === selectedStatus);
      if (selectedAgent !== "all") tasks = tasks.filter(task => task.agent === selectedAgent);
      if (searchTerm) {
        const q = searchTerm.toLowerCase();
        tasks = tasks.filter(task =>
          String(task.agent || "").toLowerCase().includes(q) ||
          String(task.task || "").toLowerCase().includes(q) ||
          String(task.task_dir || "").toLowerCase().includes(q) ||
          blockedGtFiles(task).some(file => String(file).toLowerCase().includes(q))
        );
      }
      tasks.sort((a, b) => {
        if (sortMode === "status") return String(a.status || "").localeCompare(String(b.status || ""));
        if (sortMode === "agent") return String(a.agent || "").localeCompare(String(b.agent || "")) || String(a.task || "").localeCompare(String(b.task || ""));
        if (sortMode === "primer") return Number(Boolean(b.primer_read)) - Number(Boolean(a.primer_read));
        if (sortMode === "rag") return Number(b.rag_tool_calls || 0) - Number(a.rag_tool_calls || 0);
        if (sortMode === "tools") {
          return (Number(b.total_tool_calls || 0) + Number(b.pseudo_tool_calls || 0)) -
            (Number(a.total_tool_calls || 0) + Number(a.pseudo_tool_calls || 0));
        }
        return Number(b.elapsed_seconds || 0) - Number(a.elapsed_seconds || 0);
      });
      return tasks;
    }
    function renderRows(tasks) {
      const rows = document.getElementById("rows");
      if (!tasks.length) {
        rows.innerHTML = `<tr><td colspan="12"><div class="empty">No tasks match the current filters</div></td></tr>`;
        return;
      }
      rows.innerHTML = tasks.map((task, index) => {
        const status = task.status || "pending";
        const group = statusGroup(status);
        const latestErr = lines(task.latest_stderr);
        const latestOut = latestExcerpt(task.latest_agent_response) || latestExcerpt(lines(task.latest_stdout));
        const latest = latestErr || latestOut || "";
        const latestClass = latestErr ? "latest err" : "latest";
        return `<tr>
          <td class="rank">${esc(index + 1)}</td>
          <td>${esc(task.agent)}</td>
          <td>
            <div class="task-name">${esc(task.task)}</div>
            <div class="task-dir">${esc(task.task_dir || "")}</div>
            <div class="blocked-gt" title="${esc(blockedGtFiles(task).join(", ") || "none")}">${esc(blockedGtSummary(task))}</div>
          </td>
          <td>
            <span class="stat ${group}"><i class="mark"></i>${esc(status)}</span>
            ${status === "running" ? `<div><span class="pbar"><i></i></span></div>` : ""}
          </td>
          <td>${fmtElapsed(task.elapsed_seconds)}</td>
          <td>${primerCell(task)}</td>
          <td>${ragCell(ragCount(task, "search_navigator"))}</td>
          <td>${ragCell(ragCount(task, "search_schema"))}</td>
          <td>${ragCell(ragCount(task, "search_technical"))}</td>
          <td><div class="tools">${topTools(task) || `<span class="muted">--</span>`}</div></td>
          <td><div class="${latestClass}">${esc(latest || "--")}</div></td>
          <td><button class="log-btn" data-agent="${esc(task.agent)}" data-task="${esc(task.task)}">Open Log</button></td>
        </tr>`;
      }).join("");
      document.querySelectorAll(".log-btn[data-agent]").forEach(button => {
        button.addEventListener("click", () => openLog(button.dataset.agent, button.dataset.task));
      });
    }
    function render() {
      document.getElementById("run-name").textContent = currentData.run_name || "Run";
      document.getElementById("updated-at").textContent = currentData.updated ? `Updated ${currentData.updated}` : "Updated --";
      renderAgentCards(currentData.tasks || []);
      renderFilters(currentData.tasks || []);
      renderRows(filteredTasks());
    }
    async function refresh() {
      const response = await fetch("/api/status", { cache: "no-store" });
      currentData = await response.json();
      render();
    }
    async function openLog(agent, task) {
      const modal = document.getElementById("log-modal");
      document.getElementById("log-title").textContent = `${task}`;
      document.getElementById("log-meta").textContent = `${agent} | loading conversation log`;
      document.getElementById("conversation").innerHTML = `<div class="empty">Loading conversation log</div>`;
      modal.classList.add("open");
      const url = `/api/conversation?agent=${encodeURIComponent(agent)}&task=${encodeURIComponent(task)}`;
      const response = await fetch(url, { cache: "no-store" });
      const payload = await response.json();
      const blocked = Array.isArray(payload.blocked_gt_xml_filenames) ? payload.blocked_gt_xml_filenames : [];
      const blockedText = blocked.length ? blocked.join(", ") : "none";
      document.getElementById("log-meta").textContent = `${payload.agent || agent} | ${payload.task_dir || ""} | blocked GT: ${blockedText}`;
      if (payload.error) {
        lastConversationText = payload.error;
        document.getElementById("conversation").innerHTML = `<div class="empty">${esc(payload.error)}</div>`;
        return;
      }
      const entries = payload.entries || [];
      lastConversationText = entries.map(entry => `[${entry.label}]\\n${entry.text}`).join("\\n\\n");
      document.getElementById("conversation").innerHTML = entries.length ? entries.map(entry => `
        <section class="entry">
          <div class="entry-label">${esc(entry.label)}</div>
          <pre class="entry-text">${esc(entry.text)}</pre>
        </section>
      `).join("") : `<div class="empty">No conversation events recorded yet</div>`;
    }
    function closeLog() {
      document.getElementById("log-modal").classList.remove("open");
    }
    document.getElementById("search").addEventListener("input", event => {
      searchTerm = event.target.value.trim();
      render();
    });
    document.getElementById("agent-filter").addEventListener("change", event => {
      selectedAgent = event.target.value;
      render();
    });
    document.getElementById("sort-mode").addEventListener("change", event => {
      sortMode = event.target.value;
      render();
    });
    document.getElementById("close-log").addEventListener("click", closeLog);
    document.getElementById("log-modal").addEventListener("click", event => {
      if (event.target.id === "log-modal") closeLog();
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape") closeLog();
    });
    document.getElementById("copy-log").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(lastConversationText); } catch {}
    });
    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""


def start_dashboard_server(
    *,
    run_name: str,
    agent_keys: list[str],
    task_names: list[str],
    blocked_gt_by_task: dict[str, list[str]],
    host: str,
    port: int,
) -> tuple[ThreadingHTTPServer, str]:
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/status":
                payload = collect_dashboard_snapshot(
                    run_name,
                    agent_keys,
                    task_names,
                    blocked_gt_by_task,
                )
                self._send_json(200, payload)
                return

            if parsed.path == "/api/conversation":
                query = parse_qs(parsed.query)
                payload = collect_conversation_log(
                    run_name=run_name,
                    agent_keys=agent_keys,
                    agent_key=query.get("agent", [""])[0],
                    task_name=query.get("task", [""])[0],
                )
                self._send_json(200 if "error" not in payload else 400, payload)
                return

            body = dashboard_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    candidates = [port] if port == 0 else list(range(port, port + 20))
    last_error: OSError | None = None
    for candidate in candidates:
        try:
            server = ThreadingHTTPServer((host, candidate), DashboardHandler)
            break
        except OSError as exc:
            last_error = exc
    else:
        raise RuntimeError(f"Could not start dashboard server: {last_error}")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address
    display_host = "127.0.0.1" if actual_host in ("0.0.0.0", "::") else actual_host
    return server, f"http://{display_host}:{actual_port}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GEOS eval harness: runs claude_code and cursor_composer2 via Docker + acpx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--run", "-r",
        required=True,
        metavar="RUN_NAME",
        help="Name of the experiment run subfolder, e.g. experiment_run1. "
             "Results land at <agent_dir>/<run>/<task>/",
    )
    parser.add_argument(
        "--experiments-dir", "-d",
        type=Path,
        default=EXPERIMENTS_DIR,
        help=f"Directory containing task subdirs with instructions.txt "
             f"(default: {EXPERIMENTS_DIR})",
    )
    parser.add_argument(
        "--agents", "-a",
        nargs="+",
        choices=list(AGENTS.keys()),
        default=list(AGENTS.keys()),
        help="Agents to evaluate (default: all)",
    )
    parser.add_argument(
        "--include", "-i",
        nargs="+",
        metavar="TASK_NAME",
        help="Run only these tasks (default: all tasks in experiments dir)",
    )
    parser.add_argument(
        "--exclude", "-x",
        nargs="+",
        metavar="TASK_NAME",
        default=[],
        help="Skip these tasks (applied after --include)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout per task in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--pseudo-tool-retries",
        type=int,
        default=1,
        help="Retries per task when an agent prints non-executed pseudo tool invocations (default: 1)",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=2,
        help="Max concurrent docker runs (default: 2; keep low to avoid OOM)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print docker commands without executing",
    )
    parser.add_argument(
        "--results-root-dir",
        type=Path,
        default=DATA_DIR / "eval",
        help=f"Root directory for per-agent result folders "
             f"(default: {DATA_DIR / 'eval'})",
    )
    parser.add_argument(
        "--tmp-geos-parent",
        type=Path,
        default=TEMP_GEOS_PARENT,
        help=f"Directory for per-task filtered GEOS copies "
             f"(default: {TEMP_GEOS_PARENT})",
    )
    parser.add_argument(
        "--plugin-dir",
        type=Path,
        default=DEFAULT_PLUGIN_DIR,
        help=f"Claude Code plugin directory for claude_code_repo3_plugin "
             f"(default: {DEFAULT_PLUGIN_DIR})",
    )
    parser.add_argument(
        "--vector-db-dir",
        type=Path,
        default=DEFAULT_VECTOR_DB_DIR,
        help=f"Host GEOS vector DB directory mounted for repo3 RAG "
             f"(default: {DEFAULT_VECTOR_DB_DIR})",
    )
    parser.add_argument(
        "--geos-primer-path",
        type=Path,
        default=DEFAULT_GEOS_PRIMER_PATH,
        help=f"GEOS primer markdown copied into task workspaces as "
             f"{CONTAINER_GEOS_PRIMER_PATH} and explicitly read before GEOS/RAG use "
             f"(default: {DEFAULT_GEOS_PRIMER_PATH})",
    )
    parser.add_argument(
        "--claude-model",
        default=DEFAULT_CLAUDE_MODEL,
        help=f"Model slash command sent as the first prompt line for native Claude "
             f"(default: {DEFAULT_CLAUDE_MODEL})",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Serve a browser dashboard for live task status and output",
    )
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Serve the dashboard for the selected run/agents/tasks without launching experiments",
    )
    parser.add_argument(
        "--dashboard-host",
        default="127.0.0.1",
        help="Dashboard bind host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=8765,
        help="Dashboard port; if busy, the next available port is used (default: 8765)",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=GROUND_TRUTH_DIR,
        metavar="DIR",
        help=f"Directory containing per-task ground-truth subdirs whose XML filenames "
             f"will be blocked from the agent. Pass an empty string to disable. "
             f"(default: {GROUND_TRUTH_DIR})",
    )
    args = parser.parse_args()

    for agent_key, agent in AGENTS.items():
        agent["results_dir"] = args.results_root_dir / agent_key

    selected_native_claude = any(
        AGENTS[agent_key].get("runner") == "claude_native"
        for agent_key in args.agents
    )
    if selected_native_claude and not args.dashboard_only:
        if not args.plugin_dir.exists():
            print(f"{C.FAIL}Error: plugin dir not found: {args.plugin_dir}{C.ENDC}")
            sys.exit(1)
        if not (args.plugin_dir / ".claude-plugin" / "plugin.json").exists():
            print(
                f"{C.FAIL}Error: plugin manifest not found under: "
                f"{args.plugin_dir / '.claude-plugin' / 'plugin.json'}{C.ENDC}"
            )
            sys.exit(1)
        if not args.vector_db_dir.exists():
            print(f"{C.FAIL}Error: vector DB dir not found: {args.vector_db_dir}{C.ENDC}")
            sys.exit(1)
        if not args.dry_run and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            print(
                f"{C.FAIL}Error: ANTHROPIC_AUTH_TOKEN is required for "
                f"claude_code_repo3_plugin. Export it in your shell before running.{C.ENDC}"
            )
            sys.exit(1)

    if not args.dashboard_only and not args.geos_primer_path.exists():
        print(
            f"{C.WARNING}Warning: GEOS primer not found: {args.geos_primer_path}; "
            f"primer injection disabled.{C.ENDC}"
        )

    # Normalise ground-truth-dir: treat missing or empty-string as None
    ground_truth_dir: Path | None = args.ground_truth_dir
    if ground_truth_dir is not None and not ground_truth_dir.exists():
        print(
            f"{C.WARNING}Warning: --ground-truth-dir '{ground_truth_dir}' does not exist; "
            f"GT XML blocking disabled.{C.ENDC}"
        )
        ground_truth_dir = None

    experiments_dir: Path = args.experiments_dir

    # Validate experiments directory
    if not experiments_dir.exists():
        print(f"{C.FAIL}Error: experiments dir not found: {experiments_dir}{C.ENDC}")
        sys.exit(1)

    # Discover all tasks
    all_tasks = sorted(d.name for d in experiments_dir.iterdir() if d.is_dir())

    # Apply --include filter
    if args.include:
        missing = [t for t in args.include if t not in all_tasks]
        if missing:
            print(f"{C.WARNING}Warning: tasks not found in {experiments_dir}: {missing}{C.ENDC}")
        tasks = [t for t in args.include if t in all_tasks]
    else:
        tasks = all_tasks

    # Apply --exclude filter
    if args.exclude:
        excluded = set(args.exclude)
        tasks = [t for t in tasks if t not in excluded]

    if not tasks:
        print(f"{C.FAIL}No tasks to run.{C.ENDC}")
        sys.exit(1)

    blocked_gt_by_task: dict[str, list[str]] = {}
    if ground_truth_dir is not None:
        blocked_gt_by_task = {
            task: collect_ground_truth_xml_filenames(ground_truth_dir / task)
            for task in tasks
        }

    agents_context = load_agents_md()
    combos = [(task, agent) for task in tasks for agent in args.agents]

    # Show where results will land
    result_paths = {
        agent_key: AGENTS[agent_key]["results_dir"] / args.run
        for agent_key in args.agents
    }

    print(f"\n{C.BOLD}{C.HEADER}{'=' * 70}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}  GEOS Eval Harness{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 70}{C.ENDC}")
    print(f"  Run name       : {args.run}")
    print(f"  Experiments dir: {experiments_dir}")
    print(f"  Tasks          : {len(tasks)}")
    print(f"  Agents         : {args.agents}")
    print(f"  Combos         : {len(combos)}")
    print(f"  Timeout        : {args.timeout}s per task")
    print(f"  Workers        : {args.workers}")
    print(f"  Pseudo retries : {args.pseudo_tool_retries}")
    print(f"  Dry run        : {args.dry_run}")
    print(f"  GT XML blocking: {ground_truth_dir or 'disabled'}")
    print(f"  Results root   : {args.results_root_dir}")
    print(f"  Temp GEOS dir  : {args.tmp_geos_parent}")
    print(f"  GEOS primer    : {args.geos_primer_path if args.geos_primer_path.exists() else 'disabled'}")
    if selected_native_claude:
        print(f"  Plugin dir     : {args.plugin_dir}")
        print(f"  Vector DB dir  : {args.vector_db_dir}")
        print(f"  Claude model   : {args.claude_model}")
    for agent_key, path in result_paths.items():
        print(f"  Results ({agent_key}): {path}")
    print(f"  Started        : {datetime.now().isoformat()}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 70}{C.ENDC}\n")

    dashboard_server: ThreadingHTTPServer | None = None
    if args.dashboard or args.dashboard_only:
        try:
            dashboard_server, dashboard_url = start_dashboard_server(
                run_name=args.run,
                agent_keys=args.agents,
                task_names=tasks,
                blocked_gt_by_task=blocked_gt_by_task,
                host=args.dashboard_host,
                port=args.dashboard_port,
            )
            print(f"{C.CYAN}Dashboard:{C.ENDC} {dashboard_url}\n")
        except Exception as exc:
            print(f"{C.FAIL}Error: failed to start dashboard: {exc}{C.ENDC}")
            sys.exit(1)

    if args.dashboard_only:
        assert dashboard_server is not None
        print(f"{C.CYAN}Dashboard-only mode:{C.ENDC} no experiments will be launched.")
        print("Press Ctrl-C to stop the dashboard server.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nStopping dashboard server.")
            dashboard_server.shutdown()
        return

    results: list[dict] = []

    executor = ThreadPoolExecutor(max_workers=args.workers)
    futures = {
        executor.submit(
            run_task,
            task_name=task,
            agent_key=agent,
            agents_context=agents_context,
            experiments_dir=experiments_dir,
            run_name=args.run,
            timeout=args.timeout,
            dry_run=args.dry_run,
            pseudo_tool_retries=args.pseudo_tool_retries,
            ground_truth_dir=ground_truth_dir,
            plugin_dir=args.plugin_dir,
            vector_db_dir=args.vector_db_dir,
            geos_primer_path=args.geos_primer_path,
            claude_model=args.claude_model,
            tmp_geos_parent=args.tmp_geos_parent,
        ): (task, agent)
        for task, agent in combos
    }
    seen_futures: set[Any] = set()
    try:
        for i, future in enumerate(as_completed(futures), 1):
            seen_futures.add(future)
            task, agent = futures[future]
            try:
                result = future.result()
                results.append(result)
                status = result.get("status", "?")
                color = C.GREEN if status == "success" else (C.WARNING if status == "dry_run" else C.FAIL)
                print(f"[{i:3d}/{len(combos)}] {color}{status:<14}{C.ENDC}  {agent:<28}  {task}")
            except Exception as exc:
                results.append({"task": task, "agent": agent, "status": "error", "error": str(exc)})
                print(f"[{i:3d}/{len(combos)}] {C.FAIL}ERROR         {C.ENDC}  {agent:<28}  {task}  ({exc})")
    except KeyboardInterrupt:
        print(f"\n{C.WARNING}Interrupt received. Stopping running agents; dashboard will stay up.{C.ENDC}")
        stop_active_processes()
        for future, (task, agent) in futures.items():
            if future.cancel():
                results.append({"task": task, "agent": agent, "status": "cancelled"})
        executor.shutdown(wait=True, cancel_futures=True)
        for future, (task, agent) in futures.items():
            if future in seen_futures or future.cancelled():
                continue
            if future.done():
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append({"task": task, "agent": agent, "status": "error", "error": str(exc)})
            else:
                results.append({"task": task, "agent": agent, "status": "interrupted"})
    else:
        executor.shutdown(wait=True)

    # Summary
    succeeded = sum(1 for r in results if r["status"] == "success")
    failed    = sum(1 for r in results if r["status"] not in ("success", "dry_run"))
    print(f"\n{C.BOLD}Done{C.ENDC}: {C.GREEN}{succeeded} succeeded{C.ENDC}, "
          f"{C.FAIL}{failed} failed{C.ENDC} / {len(combos)} total")

    if failed:
        print(f"\n{C.FAIL}Failed tasks:{C.ENDC}")
        for r in results:
            if r["status"] not in ("success", "dry_run"):
                error_text = f": {r.get('error', '')}" if r.get("error") else ""
                print(f"  [{r['status']}] {r['agent']} / {r['task']}{error_text}")

    if dashboard_server is not None:
        print(f"\n{C.CYAN}Dashboard is still running:{C.ENDC} {dashboard_url}")
        print("Press Ctrl-C to stop the dashboard server.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nStopping dashboard server.")
            dashboard_server.shutdown()


if __name__ == "__main__":
    main()
