from pathlib import Path
from typing import List

from .base import Tool
from .file_tools import ReadFileTool, WriteFileTool
from .geos_tool import RunGeosTool
from .search_tools import SearchNavigatorTool, SearchTechnicalTool, SearchWebTool
from .fetch_code import FetchCodeTool
from .shell_tools import ListDirTool, PythonExecTool, ShellCommandTool
from .user_io import AskUser, ConfirmAction


def build_default_tools(workspace_root: Path) -> List[Tool]:
    """Build the default set of tools for the agent.

    File and shell tools are restricted to the workspace directory.
    The agent should write files directly to inputs/ and outputs/ subdirectories.
    """
    return [
        ReadFileTool(workspace_root),
        WriteFileTool(workspace_root),
        ListDirTool(workspace_root),
        ShellCommandTool(workspace_root),
        PythonExecTool(workspace_root),
        # Dual-collection search tools
        SearchNavigatorTool(),  # RST prose for navigation
        SearchTechnicalTool(),  # XML syntax lookup
        FetchCodeTool(),  # Lazy load code/XML
        SearchWebTool(),
        RunGeosTool(workspace_root),
        AskUser(),
        ConfirmAction(),
    ]
