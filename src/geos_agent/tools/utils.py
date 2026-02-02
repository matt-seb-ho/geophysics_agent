from pathlib import Path
from typing import List

from .base import Tool
from .file_tools import ReadFileTool, WriteFileTool
from .geos_tool import RunGeosTool
from .search_tools import SearchNavigatorTool, SearchTechnicalTool, SearchGeosDocsTool, SearchWebTool
from .fetch_code import FetchCodeTool
from .shell_tools import ListDirTool, PythonExecTool, ShellCommandTool


def build_default_tools(workspace_root: Path) -> List[Tool]:
    """Build the default set of tools for the agent.
    
    File and shell tools are restricted to the data/ subdirectory
    to prevent the agent from modifying source code or other files.
    """
    data_root = workspace_root / "data"
    return [
        ReadFileTool(data_root),
        WriteFileTool(data_root),
        ListDirTool(data_root),
        ShellCommandTool(data_root),
        PythonExecTool(data_root),
        # Dual-collection search tools
        SearchNavigatorTool(),    # RST prose for navigation
        SearchTechnicalTool(),    # XML syntax lookup
        SearchGeosDocsTool(),     # Legacy combined search
        FetchCodeTool(),          # Lazy load code/XML
        SearchWebTool(),
        RunGeosTool(data_root),
    ]
