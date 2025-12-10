from pathlib import Path
from typing import Any, Dict

from .base import Tool


class RunGeosTool(Tool):
    name = "run_geos"
    description = (
        "Run a GEOS simulation given an input configuration file. "
        "Currently a stub until GEOS is compiled and available."
    )
    parameters = {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": "Path to the GEOS input file (relative to workspace).",
            },
            "extra_args": {
                "type": "string",
                "description": (
                    "Additional command-line arguments for GEOS, if needed."
                ),
                "default": "",
            },
        },
        "required": ["input_path"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, input_path: str, extra_args: str = "") -> Dict[str, Any]:
        # TODO: once GEOS is compiled, call the real binary here via subprocess.
        return {
            "input_path": input_path,
            "extra_args": extra_args,
            "warning": "run_geos is currently stubbed; GEOS is not yet wired up.",
        }
