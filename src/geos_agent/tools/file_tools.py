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

    def format_execution_summary(self, path: str, max_chars: int = 4000, **kwargs) -> str:
        if max_chars != 4000:
            return f"reading '{path}' (max {max_chars} chars)"
        return f"reading '{path}'"

    def run(self, path: str, max_chars: int = 4000) -> Dict[str, Any]:
        # RAG Contamination Prevention: Block retrieval of XML files from excluded directories
        import os
        excluded_dir = os.environ.get("EXCLUDED_EXAMPLE_DIR", "").lower().strip()
        if excluded_dir:
            try:
                # Check extension
                if str(path).lower().endswith(".xml"):
                    # Check if file path contains the excluded directory string in its parent path
                    # We use a broad check to catch various path formats (absolute/relative)
                    p = Path(path)
                    # Use string representation to catch directory names in path
                    if excluded_dir in str(p.parent).lower():
                        return {
                            "error": f"Access denied: XML files from '{excluded_dir}' are restricted during this experiment.",
                            "path": str(path)
                        }
            except Exception:
                pass
                
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
        "IMPORTANT: Files can ONLY be written to 'inputs/' or 'outputs/' directories. "
        "Use 'inputs/' for GEOS XML input files and configuration files. "
        "Use 'outputs/' for simulation results and output data. "
        "Example: path='inputs/simulation.xml' or path='outputs/results.txt'"
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Path to the file, relative to the workspace root. "
                    "MUST start with 'inputs/' or 'outputs/'. "
                    "Examples: 'inputs/simulation.xml', 'outputs/results.txt'"
                ),
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

    def format_execution_summary(self, path: str, content: str, overwrite: bool = True, **kwargs) -> str:
        size = len(content) if isinstance(content, str) else 0
        mode = "overwriting" if overwrite else "appending to"
        return f"{mode} '{path}' ({size} chars)"

    def run(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        abs_path = (self.workspace_root / path).resolve()
        if not str(abs_path).startswith(str(self.workspace_root)):
            return {"error": "Attempted to write outside of workspace."}

        # Enforce that writes must go to inputs/ or outputs/ subdirectories
        rel_path = Path(path)
        path_parts = rel_path.parts
        if len(path_parts) == 0:
            return {"error": "Path cannot be empty."}

        first_dir = path_parts[0]
        if first_dir not in ("inputs", "outputs"):
            return {
                "error": f"Files can only be written to 'inputs/' or 'outputs/' directories. "
                f"Path '{path}' starts with '{first_dir}/' which is not allowed. "
                f"Use path='inputs/{path}' for input files or path='outputs/{path}' for output files."
            }

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
