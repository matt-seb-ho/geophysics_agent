import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from geos_agent.tools.base import Tool


class ListDirTool(Tool):
    name = "list_dir"
    description = (
        "List files and directories inside a folder in the workspace. "
        "Use this to discover available examples, inputs, and outputs."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Directory path, relative to the workspace root. "
                    "Use '.' for the workspace root."
                ),
                "default": ".",
            }
        },
        "required": [],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, path: str = ".") -> Dict[str, Any]:
        abs_dir = (self.workspace_root / path).resolve()
        if not str(abs_dir).startswith(str(self.workspace_root)):
            return {"error": "Attempted to list outside of workspace."}

        if not abs_dir.exists():
            return {"error": f"Directory does not exist: {path}"}
        if not abs_dir.is_dir():
            return {"error": f"Not a directory: {path}"}

        entries = []
        for entry in sorted(abs_dir.iterdir()):
            entries.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size_bytes": entry.stat().st_size if entry.is_file() else None,
                }
            )
        return {"path": path, "entries": entries}


class ShellCommandTool(Tool):
    name = "run_shell"
    description = (
        "Run a shell command in the workspace. "
        "Use this to execute Python scripts, compile code, or run GEOS commands "
        "once they are wired up. Be careful: commands can modify files."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": (
                    "The shell command to run. Example: 'python3 script.py --help'"
                ),
            },
            "timeout_sec": {
                "type": "number",
                "description": "Maximum seconds to allow the command to run.",
                "default": 60.0,
            },
        },
        "required": ["command"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, command: str, timeout_sec: float = 60.0) -> Dict[str, Any]:
        try:
            # Use shlex.split for safer argument parsing
            args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Failed to parse command: {e}"}

        try:
            proc = subprocess.run(
                args,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return {
                "command": command,
                "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
        except subprocess.TimeoutExpired as e:
            return {
                "command": command,
                "error": f"Command timed out after {timeout_sec} seconds",
                "stdout": e.stdout[-4000:] if e.stdout else "",
                "stderr": e.stderr[-4000:] if e.stderr else "",
            }
        except Exception as e:
            return {"command": command, "error": f"Failed to run command: {e!r}"}


class PythonExecTool(Tool):
    name = "run_python_code"
    description = (
        "Execute a short Python snippet in a subprocess. "
        "Use this for small utilities or sanity checks. "
        "Prefer 'run_shell' with 'python3 script.py' for larger scripts."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Python code to execute. The result will include stdout and stderr."
                ),
            },
            "timeout_sec": {
                "type": "number",
                "description": "Maximum seconds to allow the code to run.",
                "default": 30.0,
            },
        },
        "required": ["code"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, code: str, timeout_sec: float = 30.0) -> Dict[str, Any]:
        # Write code to a temporary file in the workspace
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=self.workspace_root,
            suffix=".py",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, tmp_path],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return {
                "script_path": os.path.relpath(tmp_path, self.workspace_root),
                "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
        except subprocess.TimeoutExpired as e:
            return {
                "script_path": os.path.relpath(tmp_path, self.workspace_root),
                "error": f"Python execution timed out after {timeout_sec} seconds",
                "stdout": e.stdout[-4000:] if e.stdout else "",
                "stderr": e.stderr[-4000:] if e.stderr else "",
            }
        except Exception as e:
            return {
                "script_path": os.path.relpath(tmp_path, self.workspace_root),
                "error": f"Failed to execute Python code: {e!r}",
            }
