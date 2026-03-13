import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from geos_agent.tools.shell_tools import (
    PythonExecTool,
    _extract_import_targets,
    _parse_missing_modules,
)


class PythonExecToolTests(unittest.TestCase):
    def test_extract_import_targets_collects_imports(self) -> None:
        code = (
            "import numpy as np\n"
            "from matplotlib import pyplot\n"
            "from sklearn.model_selection import train_test_split\n"
            "from .local_module import helper\n"
        )

        self.assertEqual(
            _extract_import_targets(code),
            ["numpy", "matplotlib", "sklearn.model_selection"],
        )

    def test_parse_missing_modules(self) -> None:
        stderr = (
            "Traceback (most recent call last):\n"
            "  ...\n"
            "ModuleNotFoundError: No module named 'seaborn'\n"
        )

        self.assertEqual(_parse_missing_modules(stderr), ["seaborn"])

    def test_run_reports_missing_packages_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            workspace.joinpath("pyproject.toml").write_text(
                "[project]\nname='demo'\nversion='0.1.0'\ndependencies=[]\n",
                encoding="utf-8",
            )
            tool = PythonExecTool(workspace)

            with patch("geos_agent.tools.shell_tools.shutil.which", return_value="/usr/bin/uv"):
                with patch("geos_agent.tools.shell_tools.subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = '["seaborn"]'
                    mock_run.return_value.stderr = ""

                    result = tool.run("import seaborn\nprint('ok')", timeout_sec=5)

            self.assertEqual(result["missing_packages"], ["seaborn"])
            self.assertEqual(result["suggested_commands"], ["uv add seaborn"])
            self.assertTrue(result["needs_confirmation"])
            self.assertEqual(mock_run.call_count, 1)

    def test_run_suggests_uv_sync_for_declared_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            workspace.joinpath("pyproject.toml").write_text(
                "[project]\nname='demo'\nversion='0.1.0'\ndependencies=['matplotlib>=3.0']\n",
                encoding="utf-8",
            )
            tool = PythonExecTool(workspace)

            with patch("geos_agent.tools.shell_tools.shutil.which", return_value="/usr/bin/uv"):
                with patch("geos_agent.tools.shell_tools.subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = '["matplotlib"]'
                    mock_run.return_value.stderr = ""

                    result = tool.run("import matplotlib\nprint('ok')", timeout_sec=5)

            self.assertEqual(result["missing_packages"], ["matplotlib"])
            self.assertEqual(result["suggested_commands"], ["uv sync"])
            self.assertTrue(result["needs_confirmation"])


if __name__ == "__main__":
    unittest.main()
