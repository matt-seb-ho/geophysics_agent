import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import GeosAgent


class _PassthroughPruning:
    def __init__(self) -> None:
        self.last_stats = {"enabled": True, "active": False}

    def build_model_messages(self, messages):
        return messages


class _FakeClient:
    def __init__(self, prompt_tokens: int) -> None:
        self._usage = {"prompt_tokens": prompt_tokens}

    def get_token_usage(self) -> dict:
        return dict(self._usage)


class ContextCompactionTriggerTests(unittest.TestCase):
    def _make_agent(self, prompt_tokens: int, token_trigger: int, messages=None) -> GeosAgent:
        agent = GeosAgent.__new__(GeosAgent)
        agent.config = AgentConfig(
            context_compaction_trigger_tokens=token_trigger,
        )
        agent.client = _FakeClient(prompt_tokens)
        agent._context_pruning = _PassthroughPruning()
        agent._last_pruning_stats = {}
        agent._last_compaction_stats = {}
        agent.messages = messages or [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "short"},
            {"role": "assistant", "content": "short reply"},
            {"role": "user", "content": "follow up"},
        ]
        return agent

    def test_compaction_uses_current_context_tokens_threshold(self) -> None:
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "x" * 900_000},
            {"role": "assistant", "content": "ack"},
            {"role": "user", "content": "follow up"},
        ]
        agent = self._make_agent(
            prompt_tokens=5_000,
            token_trigger=200_000,
            messages=messages,
        )

        compacted = agent._build_model_messages()

        self.assertTrue(agent._last_compaction_stats["active"])
        self.assertEqual(agent._last_compaction_stats["cumulative_prompt_tokens"], 5_000)
        self.assertGreaterEqual(agent._last_compaction_stats["original_tokens_est"], 200_000)
        self.assertLess(len(compacted), len(agent.messages) + 1)

    def test_compaction_stays_inactive_when_current_context_is_below_threshold(self) -> None:
        agent = self._make_agent(prompt_tokens=500_000, token_trigger=200_000)

        agent._build_model_messages()

        self.assertFalse(agent._last_compaction_stats["active"])
        self.assertEqual(agent._last_compaction_stats["cumulative_prompt_tokens"], 500_000)
        self.assertLess(agent._last_compaction_stats["original_tokens_est"], 200_000)


if __name__ == "__main__":
    unittest.main()
