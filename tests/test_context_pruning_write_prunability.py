import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from geos_agent.agent_config import AgentConfig
from geos_agent.context_pruning import ContextPruningManager


def _assistant_tool_call(call_id: str, tool_name: str, arguments: dict, content: str = "") -> dict:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
            }
        ],
    }


def _tool_result(call_id: str, payload: dict) -> dict:
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(payload, ensure_ascii=False),
    }


class WritePrunabilityTests(unittest.TestCase):
    def test_write_file_is_listed_as_prunable_without_followup_read(self) -> None:
        manager = ContextPruningManager(AgentConfig())
        manager.begin_user_turn()

        raw_messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Create an XML file"},
            _assistant_tool_call(
                "w1",
                "write_file",
                {"path": "inputs/example.xml", "content": "<Problem />"},
            ),
            _tool_result("w1", {"status": "ok"}),
        ]

        manager.record_tool_result(
            "w1",
            "write_file",
            {"path": "inputs/example.xml", "content": "<Problem />"},
            2,
            3,
            raw_messages[3]["content"],
        )

        manager.build_model_messages(raw_messages)

        self.assertEqual(manager._last_prunable_tool_ids, ["w1"])

    def test_edit_file_is_listed_as_prunable_without_followup_read(self) -> None:
        manager = ContextPruningManager(AgentConfig())
        manager.begin_user_turn()

        raw_messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Patch the XML file"},
            _assistant_tool_call(
                "e1",
                "edit_file",
                {
                    "path": "inputs/example.xml",
                    "search_block": "<A/>",
                    "replace_block": "<B/>",
                },
            ),
            _tool_result("e1", {"status": "ok"}),
        ]

        manager.record_tool_result(
            "e1",
            "edit_file",
            {
                "path": "inputs/example.xml",
                "search_block": "<A/>",
                "replace_block": "<B/>",
            },
            2,
            3,
            raw_messages[3]["content"],
        )

        manager.build_model_messages(raw_messages)

        self.assertEqual(manager._last_prunable_tool_ids, ["e1"])


if __name__ == "__main__":
    unittest.main()
