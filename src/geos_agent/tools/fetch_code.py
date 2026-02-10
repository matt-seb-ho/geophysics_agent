"""
Fetch Code Tool for lazy loading code/XML content.

The agent uses this tool after search returns a pointer (xml_reference)
to read the actual file content on demand.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from .base import Tool


from ..constants import GEOS_SOURCE_DIR


class FetchCodeTool(Tool):
    name = "fetch_code"
    description = (
        "Read specific lines or sections from a code/XML file. "
        "Use this after search_geos_docs returns an xml_reference pointer. "
        "Can read entire file or a specific line range. "
        "Relative paths are resolved against GEOS_SOURCE_DIR."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read (absolute or relative to GEOS source).",
            },
            "start_line": {
                "type": "integer",
                "description": "Optional: first line to read (1-indexed). Omit to start from beginning.",
            },
            "end_line": {
                "type": "integer",
                "description": "Optional: last line to read (1-indexed, inclusive). Omit to read to end.",
            },
            "start_marker": {
                "type": "string",
                "description": "Optional: start reading after this marker string (exclusive).",
            },
            "end_marker": {
                "type": "string",
                "description": "Optional: stop reading before this marker string (exclusive).",
            },
        },
        "required": ["file_path"],
    }

    def format_execution_summary(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, **kwargs) -> str:
        path = Path(file_path)
        if start_line is not None or end_line is not None:
            line_info = f"L{start_line or 1}-L{end_line or 'end'}"
            return f"fetching code from '{path.name}' ({line_info})"
        return f"fetching code from '{path.name}'"

    def run(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        start_marker: Optional[str] = None,
        end_marker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch code from file with optional line/marker filtering."""
        
        path = Path(file_path)
        if not path.is_absolute():
            path = GEOS_SOURCE_DIR / path
        
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
        
        # If markers provided, extract section between them
        if start_marker or end_marker:
            return self._extract_by_markers(content, start_marker, end_marker, path.name)
        
        # If line range provided, extract those lines
        if start_line is not None or end_line is not None:
            return self._extract_by_lines(content, start_line, end_line, path.name)
        
        # Return entire file (with reasonable limit)
        lines = content.split("\n")
        if len(lines) > 200:
            return {
                "file": path.name,
                "content": "\n".join(lines[:200]),
                "truncated": True,
                "total_lines": len(lines),
                "hint": "File is large. Use start_line/end_line or markers to read specific sections.",
            }
        
        return {
            "file": path.name,
            "content": content,
            "total_lines": len(lines),
        }
    
    def _extract_by_markers(
        self, 
        content: str, 
        start_marker: Optional[str], 
        end_marker: Optional[str],
        filename: str,
    ) -> Dict[str, Any]:
        """Extract content between markers."""
        
        start_idx = 0
        end_idx = len(content)
        
        if start_marker:
            pos = content.find(start_marker)
            if pos == -1:
                return {"error": f"Start marker not found: {start_marker}"}
            # Start after the line containing the marker
            newline_pos = content.find("\n", pos)
            start_idx = newline_pos + 1 if newline_pos != -1 else pos + len(start_marker)
        
        if end_marker:
            pos = content.find(end_marker, start_idx)
            if pos == -1:
                return {"error": f"End marker not found: {end_marker}"}
            # End before the line containing the marker
            end_idx = content.rfind("\n", start_idx, pos)
            if end_idx == -1:
                end_idx = pos
        
        extracted = content[start_idx:end_idx].strip()
        
        return {
            "file": filename,
            "content": extracted,
            "markers_used": {
                "start": start_marker,
                "end": end_marker,
            },
        }
    
    def _extract_by_lines(
        self,
        content: str,
        start_line: Optional[int],
        end_line: Optional[int],
        filename: str,
    ) -> Dict[str, Any]:
        """Extract specific line range."""
        
        lines = content.split("\n")
        total = len(lines)
        
        start = (start_line or 1) - 1  # Convert to 0-indexed
        end = end_line or total
        
        if start < 0 or start >= total:
            return {"error": f"start_line {start_line} out of range (1-{total})"}
        if end > total:
            end = total
        
        extracted = "\n".join(lines[start:end])
        
        return {
            "file": filename,
            "content": extracted,
            "line_range": f"L{start+1}-L{end}",
            "total_lines": total,
        }
