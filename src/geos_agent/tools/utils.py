from pathlib import Path
from typing import List

from .base import Tool
from .file_tools import ReadFileTool, WriteFileTool
from .geos_tool import RunGeosTool
from .search_tools import SearchGeosDocsTool, SearchWebTool
from .shell_tools import ListDirTool, PythonExecTool, ShellCommandTool


def build_default_tools(workspace_root: Path) -> List[Tool]:
    return [
        ReadFileTool(workspace_root),
        WriteFileTool(workspace_root),
        ListDirTool(workspace_root),
        ShellCommandTool(workspace_root),
        PythonExecTool(workspace_root),
        SearchGeosDocsTool(),
        SearchWebTool(),
        RunGeosTool(workspace_root),
    ]
