import os
import subprocess
import shlex
from pathlib import Path
from typing import Any, Dict

from geos_agent.constants import GEOSX_EXECUTABLE
from .base import Tool


class RunGeosTool(Tool):
    name = "run_geos"
    description = (
        "Run a GEOS-X geophysics simulation given an input XML configuration file. "
        "Usage: geosx -i inputs/simulation.xml\n"
        "Set GEOSX_EXECUTABLE env var to change the executable path."
    )
    parameters = {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": (
                    "Path to the GEOS-X input XML file (relative to workspace). "
                    "Example: 'inputs/my_simulation.xml'"
                ),
            },
            "extra_args": {
                "type": "string",
                "description": (
                    "Additional command-line arguments for GEOS-X, if needed. "
                    "These are passed after the -i flag."
                ),
                "default": "",
            },
            "timeout_sec": {
                "type": "number",
                "description": "Maximum seconds to allow the simulation to run.",
                "default": 300.0,
            },
        },
        "required": ["input_path"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(
        self, input_path: str, extra_args: str = "", timeout_sec: float = 300.0
    ) -> Dict[str, Any]:
        # Check if GEOS-X executable exists
        if not GEOSX_EXECUTABLE.exists():
            return {
                "input_path": input_path,
                "error": (
                    f"GEOS-X executable not found at: {GEOSX_EXECUTABLE}\n\n"
                    "GEOS-X needs to be compiled from source.\n"
                    "Source code location: /data/brianliu/GEOS/\n\n"
                    "Build instructions:\n"
                    "1. cd /data/brianliu/GEOS/\n"
                    "2. mkdir build && cd build\n"
                    "3. cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local\n"
                    "4. make -j$(nproc)\n"
                    "5. make install\n\n"
                    "Or set GEOSX_EXECUTABLE env var to an existing installation:\n"
                    "export GEOSX_EXECUTABLE=/path/to/geosx"
                ),
            }

        # Validate input path
        abs_input_path = (self.workspace_root / input_path).resolve()
        if not str(abs_input_path).startswith(str(self.workspace_root)):
            return {"error": "Input path is outside of workspace."}
        if not abs_input_path.exists():
            return {"error": f"Input file does not exist: {input_path}"}

        # Build command: geosx -i <input_file> [extra_args]
        cmd = [str(GEOSX_EXECUTABLE), "-i", str(abs_input_path)]
        if extra_args:
            try:
                cmd.extend(shlex.split(extra_args))
            except ValueError as e:
                return {"error": f"Failed to parse extra_args: {e}"}

        # Run GEOS-X
        # IMPORTANT: Set LD_LIBRARY_PATH with system libraries first to avoid
        # Anaconda's older libstdc++ which causes GLIBCXX_3.4.30 version errors.
        # The GEOS-X binary has RPATH with anaconda lib before system libs, so we
        # need to override it by setting LD_LIBRARY_PATH with system libs first.
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu"

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env,
            )
            return {
                "input_path": input_path,
                "command": " ".join(cmd),
                "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
        except subprocess.TimeoutExpired as e:
            return {
                "input_path": input_path,
                "error": f"GEOS-X simulation timed out after {timeout_sec} seconds",
                "stdout": e.stdout[-4000:] if e.stdout else "",
                "stderr": e.stderr[-4000:] if e.stderr else "",
            }
        except Exception as e:
            return {
                "input_path": input_path,
                "error": f"Failed to run GEOS-X: {e!r}",
            }
