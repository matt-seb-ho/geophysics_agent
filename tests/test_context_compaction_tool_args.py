import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import GeosAgent


class ContextCompactionToolArgsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = GeosAgent.__new__(GeosAgent)
        self.agent.config = AgentConfig()

    def test_compacted_read_file_args_do_not_include_helper_keys(self) -> None:
        compacted = json.loads(
            self.agent._sanitize_tool_arguments_for_context(
                "read_file",
                json.dumps({"path": "inputs/triaxial_base.xml"}, ensure_ascii=False),
            )
        )

        self.assertEqual(compacted, {"path": "inputs/triaxial_base.xml"})
        self.assertNotIn("_compaction", compacted)

    def test_compacted_edit_file_args_preserve_schema_keys_only(self) -> None:
        compacted = json.loads(
            self.agent._sanitize_tool_arguments_for_context(
                "edit_file",
                json.dumps(
                    {
                        "path": "inputs/triaxial_base.xml",
                        "search_block": "<OldBlock>" + ("x" * 500) + "</OldBlock>",
                        "replace_block": "<NewBlock>" + ("y" * 500) + "</NewBlock>",
                    },
                    ensure_ascii=False,
                ),
            )
        )

        self.assertEqual(set(compacted.keys()), {"path", "search_block", "replace_block"})
        self.assertNotIn("_compaction", compacted)
        self.assertNotIn("search_block_preview", compacted)
        self.assertNotIn("replace_block_preview", compacted)


if __name__ == "__main__":
    unittest.main()
