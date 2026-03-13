import sys
import unittest
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

openai_stub = ModuleType("openai")
openai_stub.APIConnectionError = Exception
openai_stub.APIError = Exception
openai_stub.APITimeoutError = Exception
openai_stub.RateLimitError = Exception


class _OpenAIStub:
    def __init__(self, *args, **kwargs) -> None:
        pass


openai_stub.OpenAI = _OpenAIStub
sys.modules.setdefault("openai", openai_stub)

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import GeosAgent


class ToolResultDisplayFormattingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = GeosAgent.__new__(GeosAgent)
        self.agent.config = AgentConfig()

    def test_run_shell_output_is_prettified(self) -> None:
        formatted = self.agent._format_tool_result_for_display(
            "run_shell",
            {"command": "pytest -q"},
            {
                "command": "pytest -q",
                "returncode": 1,
                "stdout": "1 failed\n",
                "stderr": "Traceback...\n",
            },
        )

        self.assertEqual(
            formatted,
            "$ pytest -q\n"
            "exit code: 1\n"
            "\n"
            "stdout:\n"
            "1 failed\n"
            "\n"
            "stderr:\n"
            "Traceback...",
        )

    def test_read_file_prefers_raw_content(self) -> None:
        formatted = self.agent._format_tool_result_for_display(
            "read_file",
            {"path": "inputs/model.xml"},
            {
                "path": "inputs/model.xml",
                "content": "<Mesh>\n  <InternalMesh />\n</Mesh>\n",
                "start_line": 10,
                "end_line": 12,
            },
        )

        self.assertEqual(formatted, "<Mesh>\n  <InternalMesh />\n</Mesh>\n")

    def test_write_file_prefers_written_content(self) -> None:
        formatted = self.agent._format_tool_result_for_display(
            "write_file",
            {"path": "inputs/model.xml", "content": "<Problem />\n"},
            {
                "path": "inputs/model.xml",
                "status": "ok",
                "mode": "w",
                "message": "Wrote 11 chars to inputs/model.xml",
            },
        )

        self.assertEqual(formatted, "<Problem />\n")


if __name__ == "__main__":
    unittest.main()
