from pathlib import Path
from typing import Any, Dict

from .base import Tool

# ==============================
# File & shell tools
# ==============================


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a text file from the workspace. "
        "Use this to inspect input files, configs, logs, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to the workspace root.",
            },
            "max_chars": {
                "type": "integer",
                "description": (
                    "Maximum number of characters to return. "
                    "Use a smaller limit if the file might be very large."
                ),
                "default": 4000,
            },
        },
        "required": ["path"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, path: str, max_chars: int = 4000) -> Dict[str, Any]:
        abs_path = (self.workspace_root / path).resolve()
        if not str(abs_path).startswith(str(self.workspace_root)):
            return {"error": "Attempted to read outside of workspace."}

        if not abs_path.exists():
            return {"error": f"File does not exist: {path}"}
        try:
            text = abs_path.read_text(encoding="utf-8", errors="replace")
            if len(text) > max_chars:
                text = text[:max_chars] + "\n...[truncated]..."
            return {"path": path, "content": text}
        except Exception as e:
            return {"error": f"Failed to read file {path}: {e!r}"}


class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Write text to a file in the workspace. "
        "Use this to create or modify GEOS input files, scripts, or configs."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to the workspace root.",
            },
            "content": {
                "type": "string",
                "description": "The full file content to write.",
            },
            "overwrite": {
                "type": "boolean",
                "description": (
                    "If true, overwrite the file completely. "
                    "If false and the file exists, append to the end."
                ),
                "default": True,
            },
        },
        "required": ["path", "content"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        abs_path = (self.workspace_root / path).resolve()
        if not str(abs_path).startswith(str(self.workspace_root)):
            return {"error": "Attempted to write outside of workspace."}

        abs_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if overwrite or not abs_path.exists() else "a"
        try:
            with abs_path.open(mode, encoding="utf-8") as f:
                f.write(content)
            return {
                "path": path,
                "status": "ok",
                "mode": mode,
                "message": f"Wrote {len(content)} chars to {path}",
            }
        except Exception as e:
            return {"error": f"Failed to write file {path}: {e!r}"}
