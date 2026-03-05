from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from .base import Tool
from ..constants import GEOS_SOURCE_DIR, GEOSDATA_SOURCE_DIR, MAX_READ_LINES

# ==============================
# File tools pipeline
# ==============================


class FileToolsPipeline:
    """File pipeline used by file-oriented tools."""

    def __init__(self, workspace_root: Path, llm: Any = None):
        self.llm = llm
        self.context: List[str] = []
        self.workspace_root = Path(workspace_root).resolve()

    def _resolve_read_path(self, path: str) -> Optional[Path]:
        p = Path(path)
        if p.is_absolute():
            return p if p.exists() else None

        p_workspace = (self.workspace_root / p).resolve()
        if p_workspace.exists() and str(p_workspace).startswith(str(self.workspace_root)):
            return p_workspace

        p_geos = GEOS_SOURCE_DIR / p
        if p_geos.exists():
            return p_geos

        p_geosdata = GEOSDATA_SOURCE_DIR / p
        if p_geosdata.exists():
            return p_geosdata

        return None

    def _resolve_dir(self, directory: str) -> Optional[Path]:
        d = Path(directory)
        if d.is_absolute():
            return d if d.exists() and d.is_dir() else None

        d_workspace = (self.workspace_root / d).resolve()
        if d_workspace.exists() and d_workspace.is_dir() and str(d_workspace).startswith(str(self.workspace_root)):
            return d_workspace

        d_geos = GEOS_SOURCE_DIR / d
        if d_geos.exists() and d_geos.is_dir():
            return d_geos

        d_geosdata = GEOSDATA_SOURCE_DIR / d
        if d_geosdata.exists() and d_geosdata.is_dir():
            return d_geosdata

        return None

    def _validate_write_path(self, filepath: str) -> Dict[str, Any]:
        abs_path = (self.workspace_root / filepath).resolve()
        if not str(abs_path).startswith(str(self.workspace_root)):
            return {"error": "Attempted to write outside of workspace."}

        rel_path = Path(filepath)
        path_parts = rel_path.parts
        if len(path_parts) == 0:
            return {"error": "Path cannot be empty."}

        first_dir = path_parts[0]
        if first_dir not in ("inputs", "outputs"):
            return {
                "error": (
                    "Files can only be written to 'inputs/' or 'outputs/' directories. "
                    f"Path '{filepath}' starts with '{first_dir}/' which is not allowed. "
                    f"Use path='inputs/{filepath}' for input files or path='outputs/{filepath}' for output files."
                )
            }
        return {"abs_path": abs_path}

    def _extract_by_markers(
        self,
        content: str,
        start_marker: Optional[str],
        end_marker: Optional[str],
    ) -> Dict[str, Any]:
        start_idx = 0
        end_idx = len(content)

        if start_marker:
            pos = content.find(start_marker)
            if pos == -1:
                return {"error": f"Start marker not found: {start_marker}"}
            newline_pos = content.find("\n", pos)
            start_idx = newline_pos + 1 if newline_pos != -1 else pos + len(start_marker)

        if end_marker:
            pos = content.find(end_marker, start_idx)
            if pos == -1:
                return {"error": f"End marker not found: {end_marker}"}
            end_idx = content.rfind("\n", start_idx, pos)
            if end_idx == -1:
                end_idx = pos

        return {
            "content": content[start_idx:end_idx].strip(),
            "markers_used": {"start": start_marker, "end": end_marker},
        }

    def _cap_content_lines(self, content: str) -> Dict[str, Any]:
        lines = content.split("\n")
        total = len(lines)
        if total <= MAX_READ_LINES:
            return {
                "content": content,
                "returned_lines": total,
                "truncated_by_line_limit": False,
                "max_read_lines": MAX_READ_LINES,
            }

        capped = "\n".join(lines[: MAX_READ_LINES])
        return {
            "content": capped + "\n...[truncated: line limit]...",
            "returned_lines": MAX_READ_LINES,
            "total_lines": total,
            "truncated_by_line_limit": True,
            "max_read_lines": MAX_READ_LINES,
        }

    def _extract_by_lines(
        self,
        content: str,
        start_line: Optional[int],
        end_line: Optional[int],
    ) -> Dict[str, Any]:
        lines = content.split("\n")
        total = len(lines)

        start = (start_line or 1) - 1
        end = end_line or total

        if start < 0 or start >= total:
            return {"error": f"start_line {start_line} out of range (1-{total})"}
        if end > total:
            end = total

        return {
            "content": "\n".join(lines[start:end]),
            "line_range": f"L{start + 1}-L{end}",
            "total_lines": total,
        }

    # ==========================================
    # TOOL 1: SEARCH (GREP)
    # ==========================================
    def grep_search(self, regex_pattern: str, directory: str = "./") -> Dict[str, Any]:
        target_dir = self._resolve_dir(directory)
        if target_dir is None:
            return {"error": f"Directory not found: {directory}"}

        if shutil.which("rg"):
            cmd = ["rg", "-n", "--no-heading", "--color", "never", regex_pattern, str(target_dir)]
        else:
            cmd = ["grep", "-rEn", regex_pattern, str(target_dir)]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except Exception as e:
            return {"error": f"grep search failed: {e!r}"}

        output = proc.stdout.strip()
        if not output:
            return {"pattern": regex_pattern, "directory": str(target_dir), "results": []}

        results = []
        for line in output.splitlines():
            parts = line.split(":", 2)
            if len(parts) < 2:
                continue
            filepath = parts[0]
            try:
                line_number = int(parts[1])
            except ValueError:
                continue
            preview = parts[2] if len(parts) > 2 else ""
            results.append(
                {
                    "filepath": filepath,
                    "line_number": line_number,
                    "preview": preview[:200],
                }
            )

        return {
            "pattern": regex_pattern,
            "directory": str(target_dir),
            "results": results,
            "count": len(results),
        }

    # ==========================================
    # TOOL 2: READ
    # ==========================================
    def read_file(
        self,
        filepath: str,
        max_chars: int = 4000,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        start_marker: Optional[str] = None,
        end_marker: Optional[str] = None,
    ) -> Dict[str, Any]:
        # RAG contamination prevention
        import os
        excluded_dir = os.environ.get("EXCLUDED_EXAMPLE_DIR", "").lower().strip()
        if excluded_dir:
            try:
                fp_lower = str(filepath).lower()
                if fp_lower.endswith(".xml") or fp_lower.endswith(".rst"):
                    p = Path(filepath)
                    if excluded_dir in str(p.parent).lower():
                        ext = p.suffix.lstrip(".").upper() or "FILE"
                        return {
                            "error": f"Access denied: {ext} files from '{excluded_dir}' are restricted during this experiment.",
                            "path": str(filepath),
                        }
            except Exception:
                pass

        resolved_path = self._resolve_read_path(filepath)
        if resolved_path is None:
            p = Path(filepath)
            return {
                "error": f"File not found: {filepath}",
                "checked_locations": [
                    str((self.workspace_root / p).resolve()) if not p.is_absolute() else str(p),
                    str(GEOS_SOURCE_DIR / p) if not p.is_absolute() else None,
                    str(GEOSDATA_SOURCE_DIR / p) if not p.is_absolute() else None,
                ],
            }

        try:
            text = resolved_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": f"Failed to read file {filepath}: {e!r}"}

        result: Dict[str, Any] = {"path": filepath, "resolved_path": str(resolved_path)}

        if start_marker or end_marker:
            extracted = self._extract_by_markers(text, start_marker, end_marker)
            result.update(extracted)
            if "error" in extracted:
                return result
            result.update(self._cap_content_lines(result.get("content", "")))
            return result

        if start_line is not None or end_line is not None:
            extracted = self._extract_by_lines(text, start_line, end_line)
            result.update(extracted)
            if "error" in extracted:
                return result
            result.update(self._cap_content_lines(result.get("content", "")))
            return result

        line_capped = self._cap_content_lines(text)
        result.update(line_capped)

        content_for_chars = result.get("content", "")
        if len(content_for_chars) > max_chars:
            result.update(
                {
                    "content": content_for_chars[:max_chars] + "\n...[truncated]...",
                    "truncated": True,
                    "total_chars": len(content_for_chars),
                }
            )
            return result

        result.update({"total_chars": len(content_for_chars)})
        return result

    # ==========================================
    # TOOL 3: WRITE & EDIT
    # ==========================================
    def edit_file(
        self,
        filepath: str,
        search_block: str,
        replace_block: str,
        replace_all: bool = False,
    ) -> Dict[str, Any]:
        validated = self._validate_write_path(filepath)
        if "error" in validated:
            return validated
        abs_path: Path = validated["abs_path"]

        if not abs_path.exists():
            return {"error": f"File does not exist: {filepath}"}

        try:
            file_content = abs_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": f"Failed to read file {filepath}: {e!r}"}

        if search_block not in file_content:
            return {"error": "Search block not found.", "path": filepath}

        count = file_content.count(search_block)
        new_content = (
            file_content.replace(search_block, replace_block)
            if replace_all
            else file_content.replace(search_block, replace_block, 1)
        )

        try:
            abs_path.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return {"error": f"Failed to edit file {filepath}: {e!r}"}

        return {
            "path": filepath,
            "status": "ok",
            "replacements": count if replace_all else 1,
            "available_matches": count,
            "message": "Edit applied successfully.",
        }

    def write_file(self, filepath: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        validated = self._validate_write_path(filepath)
        if "error" in validated:
            return validated
        abs_path: Path = validated["abs_path"]

        abs_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if overwrite or not abs_path.exists() else "a"
        try:
            with abs_path.open(mode, encoding="utf-8") as f:
                f.write(content)
            return {
                "path": filepath,
                "status": "ok",
                "mode": mode,
                "message": f"Wrote {len(content)} chars to {filepath}",
            }
        except Exception as e:
            return {"error": f"Failed to write file {filepath}: {e!r}"}

    # ==========================================
    # MAIN AGENT WORKFLOW (optional helper)
    # ==========================================
    def execute_task(self, user_prompt: str) -> str:
        return (
            "FileToolsPipeline is available. "
            "This method is a placeholder; orchestration is handled by tool-calling in GeosAgent."
        )


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read text/code/XML files with optional line-range or marker extraction. "
        "Supports workspace paths plus GEOS source/data relative paths."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Path to the file. Can be absolute, relative to workspace, "
                    "or relative to GEOS source/data roots."
                ),
            },
            "max_chars": {
                "type": "integer",
                "description": (
                    "Maximum number of characters to return. "
                    "Use a smaller limit if the file might be very large."
                ),
                "default": 4000,
            },
            "start_line": {
                "type": "integer",
                "description": "Optional: first line to read (1-indexed).",
            },
            "end_line": {
                "type": "integer",
                "description": "Optional: last line to read (1-indexed, inclusive).",
            },
            "start_marker": {
                "type": "string",
                "description": "Optional: start reading after this marker line (exclusive).",
            },
            "end_marker": {
                "type": "string",
                "description": "Optional: stop reading before this marker line (exclusive).",
            },
        },
        "required": ["path"],
    }

    def __init__(self, workspace_root: Path):
        self.file_pipeline = FileToolsPipeline(workspace_root=workspace_root)

    def format_execution_summary(
        self,
        path: str,
        max_chars: int = 4000,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        start_marker: Optional[str] = None,
        end_marker: Optional[str] = None,
        **kwargs,
    ) -> str:
        if start_line is not None or end_line is not None:
            return f"reading '{path}' (L{start_line or 1}-L{end_line or 'end'})"
        if start_marker or end_marker:
            return f"reading '{path}' (marker-bounded)"
        if max_chars != 4000:
            return f"reading '{path}' (max {max_chars} chars)"
        return f"reading '{path}'"

    def run(
        self,
        path: str,
        max_chars: int = 4000,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        start_marker: Optional[str] = None,
        end_marker: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.file_pipeline.read_file(
            filepath=path,
            max_chars=max_chars,
            start_line=start_line,
            end_line=end_line,
            start_marker=start_marker,
            end_marker=end_marker,
        )


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
        self.file_pipeline = FileToolsPipeline(workspace_root=workspace_root)

    def format_execution_summary(self, path: str, content: str, overwrite: bool = True, **kwargs) -> str:
        size = len(content) if isinstance(content, str) else 0
        mode = "overwriting" if overwrite else "appending to"
        return f"{mode} '{path}' ({size} chars)"

    def run(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        return self.file_pipeline.write_file(filepath=path, content=content, overwrite=overwrite)


class EditFileTool(Tool):
    name = "edit_file"
    description = (
        "Edit an existing file via exact block replacement (fast apply). "
        "Finds `search_block` and replaces it with `replace_block`."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to workspace root. Must be in inputs/ or outputs/.",
            },
            "search_block": {
                "type": "string",
                "description": "Exact text block to find in the file.",
            },
            "replace_block": {
                "type": "string",
                "description": "Replacement text block.",
            },
            "replace_all": {
                "type": "boolean",
                "description": "If true, replace all matches; otherwise replace only the first match.",
                "default": False,
            },
        },
        "required": ["path", "search_block", "replace_block"],
    }

    def __init__(self, workspace_root: Path):
        self.file_pipeline = FileToolsPipeline(workspace_root=workspace_root)

    def format_execution_summary(
        self,
        path: str,
        search_block: str,
        replace_block: str,
        replace_all: bool = False,
        **kwargs,
    ) -> str:
        mode = "all matches" if replace_all else "first match"
        return f"editing '{path}' ({mode})"

    def run(
        self,
        path: str,
        search_block: str,
        replace_block: str,
        replace_all: bool = False,
    ) -> Dict[str, Any]:
        return self.file_pipeline.edit_file(
            filepath=path,
            search_block=search_block,
            replace_block=replace_block,
            replace_all=replace_all,
        )


class GrepSearchTool(Tool):
    name = "grep_search"
    description = (
        "Search code/text using grep-style regex over a directory and return file/line matches."
    )
    parameters = {
        "type": "object",
        "properties": {
            "regex_pattern": {
                "type": "string",
                "description": "Regex pattern to search for.",
            },
            "directory": {
                "type": "string",
                "description": "Directory to search in (default './').",
                "default": "./",
            },
        },
        "required": ["regex_pattern"],
    }

    def __init__(self, workspace_root: Path):
        self.file_pipeline = FileToolsPipeline(workspace_root=workspace_root)

    def format_execution_summary(self, regex_pattern: str, directory: str = "./", **kwargs) -> str:
        return f"grep searching '{regex_pattern}' in '{directory}'"

    def run(self, regex_pattern: str, directory: str = "./") -> Dict[str, Any]:
        return self.file_pipeline.grep_search(regex_pattern=regex_pattern, directory=directory)
