import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from geos_agent.tools.base import Tool


MISSING_MODULE_RE = re.compile(
    r"(?:ModuleNotFoundError|ImportError): No module named ['\"]([^'\"]+)['\"]"
)
REQUIREMENT_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
DEPENDENCIES_BLOCK_RE = re.compile(r"(?ms)^\s*dependencies\s*=\s*\[(.*?)\]")
STRING_LITERAL_RE = re.compile(r"""['"]([^'"]+)['"]""")


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _extract_import_targets(code: str) -> List[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    targets: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.extend(alias.name for alias in node.names if alias.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            targets.append(node.module)
    return _dedupe_preserve_order(targets)


def _parse_missing_modules(stderr: str) -> List[str]:
    matches = [match.group(1) for match in MISSING_MODULE_RE.finditer(stderr or "")]
    return _dedupe_preserve_order(matches)


def _module_names_to_package_names(module_names: List[str]) -> List[str]:
    return _dedupe_preserve_order(
        [name.split(".", 1)[0] for name in module_names if name]
    )


def _read_declared_dependency_names(pyproject_path: Path) -> set[str]:
    if not pyproject_path.exists():
        return set()

    try:
        content = pyproject_path.read_text(encoding="utf-8")
    except OSError:
        return set()

    match = DEPENDENCIES_BLOCK_RE.search(content)
    if not match:
        return set()

    dependencies = STRING_LITERAL_RE.findall(match.group(1))
    names: set[str] = set()
    for requirement in dependencies:
        match = REQUIREMENT_NAME_RE.match(str(requirement))
        if match:
            names.add(match.group(1).lower().replace("_", "-"))
    return names


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

    def format_execution_summary(self, path: str = ".", **kwargs) -> str:
        return f"listing directory '{path}'"

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

    def format_execution_summary(self, command: str, timeout_sec: float = 60.0, **kwargs) -> str:
        # Truncate long commands
        cmd_display = command[:80] + "..." if len(command) > 80 else command
        if timeout_sec != 60.0:
            return f"executing '{cmd_display}' (timeout: {timeout_sec}s)"
        return f"executing '{cmd_display}'"

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

    def format_execution_summary(self, code: str, timeout_sec: float = 30.0, **kwargs) -> str:
        lines = code.count('\n') + 1 if code else 0
        return f"executing {lines} lines of Python"

    def _python_command_prefix(self, use_uv: bool) -> List[str]:
        if use_uv:
            # Avoid implicit environment syncing here so missing imports surface quickly.
            return ["uv", "run", "--no-sync", "python"]
        return [sys.executable]

    def _detect_missing_imports(
        self,
        import_targets: List[str],
        command_prefix: List[str],
        timeout_sec: float,
    ) -> List[str]:
        if not import_targets:
            return []

        checker = (
            "import importlib.util, json, sys\n"
            "missing = []\n"
            "for name in sys.argv[1:]:\n"
            "    try:\n"
            "        found = importlib.util.find_spec(name) is not None\n"
            "    except Exception:\n"
            "        found = False\n"
            "    if not found:\n"
            "        missing.append(name)\n"
            "print(json.dumps(missing))\n"
        )
        try:
            proc = subprocess.run(
                command_prefix + ["-c", checker, *import_targets],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=min(timeout_sec, 10.0),
            )
        except (subprocess.TimeoutExpired, OSError):
            return []

        if proc.returncode != 0:
            return []

        try:
            missing = json.loads(proc.stdout.strip() or "[]")
        except json.JSONDecodeError:
            return []

        if not isinstance(missing, list):
            return []
        return _dedupe_preserve_order([str(name) for name in missing if str(name).strip()])

    def _missing_package_result(
        self,
        tmp_path: str,
        missing_modules: List[str],
        declared_dependencies: set[str],
        use_uv: bool,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 1,
        source: str = "runtime",
    ) -> Dict[str, Any]:
        package_names = _module_names_to_package_names(missing_modules)
        normalized = {name.lower().replace("_", "-"): name for name in package_names}
        already_declared = [
            name for key, name in normalized.items() if key in declared_dependencies
        ]
        install_candidates = [
            name for key, name in normalized.items() if key not in declared_dependencies
        ]

        suggested_commands: List[str] = []
        if use_uv and already_declared:
            suggested_commands.append("uv sync")
        if use_uv and install_candidates:
            suggested_commands.append(
                "uv add " + " ".join(shlex.quote(name) for name in install_candidates)
            )

        guidance = (
            "Missing Python dependencies detected before execution."
            if source == "preflight"
            else "Missing Python dependencies detected while executing the snippet."
        )
        if suggested_commands:
            guidance += (
                " Ask the user for confirmation with confirm_action before running "
                f"{' or '.join(suggested_commands)}, then retry run_python_code."
            )

        return {
            "script_path": os.path.relpath(tmp_path, self.workspace_root),
            "returncode": returncode,
            "error": guidance,
            "missing_modules": missing_modules,
            "missing_packages": package_names,
            "environment": "uv" if use_uv else "python",
            "suggested_commands": suggested_commands,
            "needs_confirmation": bool(suggested_commands),
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
        }

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
            # Check if we should use 'uv run'
            # We use it if 'uv' is installed AND we are in a project root (has pyproject.toml)
            # This ensures imported dependencies work.
            use_uv = False
            pyproject_path = self.workspace_root / "pyproject.toml"
            if pyproject_path.exists() and shutil.which("uv"):
                use_uv = True

            declared_dependencies = (
                _read_declared_dependency_names(pyproject_path) if use_uv else set()
            )
            cmd_prefix = self._python_command_prefix(use_uv)

            missing_preflight = self._detect_missing_imports(
                _extract_import_targets(code),
                cmd_prefix,
                timeout_sec,
            )
            if missing_preflight:
                return self._missing_package_result(
                    tmp_path=tmp_path,
                    missing_modules=missing_preflight,
                    declared_dependencies=declared_dependencies,
                    use_uv=use_uv,
                    stderr="Preflight import check failed due to missing modules.",
                    source="preflight",
                )

            cmd = cmd_prefix + [tmp_path]

            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            runtime_missing = _parse_missing_modules(proc.stderr)
            if runtime_missing:
                return self._missing_package_result(
                    tmp_path=tmp_path,
                    missing_modules=runtime_missing,
                    declared_dependencies=declared_dependencies,
                    use_uv=use_uv,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    returncode=proc.returncode,
                    source="runtime",
                )
            result = {
                "script_path": os.path.relpath(tmp_path, self.workspace_root),
                "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
        except subprocess.TimeoutExpired as e:
            result = {
                "script_path": os.path.relpath(tmp_path, self.workspace_root),
                "error": f"Python execution timed out after {timeout_sec} seconds",
                "stdout": e.stdout[-4000:] if e.stdout else "",
                "stderr": e.stderr[-4000:] if e.stderr else "",
            }
        except Exception as e:
            result = {
                "script_path": os.path.relpath(tmp_path, self.workspace_root),
                "error": f"Failed to execute Python code: {e!r}",
            }
        finally:
            # Clean up the temporary file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # File may already be deleted or not exist

        return result
