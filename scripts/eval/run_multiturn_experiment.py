#!/usr/bin/env python3
"""
Run a single multi-turn evaluation experiment.

Orchestrates the conversation between a UserSimulator (LLM) and a GeosAgent
(in interactive mode). The simulator holds the full task specification and
drip-feeds it to the agent across multiple turns, answering questions and
providing follow-up instructions.

Usage:
    # Run a single experiment
    uv run python scripts/eval/run_multiturn_experiment.py \
        --experiment-dir data/eval/experiments_subset/ExampleEDPWellbore

    # With custom models and limits
    uv run python scripts/eval/run_multiturn_experiment.py \
        --experiment-dir data/eval/experiments_subset/ExampleEDPWellbore \
        --agent-model "moonshotai/kimi-k2.5" \
        --simulator-model "anthropic/claude-sonnet-4" \
        --max-total-turns 15 \
        --log-dir data/eval/multiturn_logs
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add scripts/eval to path so we can import user_simulator
sys.path.insert(0, str(Path(__file__).parent))

from user_simulator import SimulatorConfig, UserSimulator


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_EVAL_PREAMBLE = """\
You are being evaluated on your ability to author GEOS XML input files \
based on a user's natural language instructions. Use the documentation \
search tools (search_navigator, search_technical, fetch_code) to learn \
GEOS XML syntax and patterns, then author the configuration files yourself. \
If a tool blocks access to a file, move on and rely on documentation search \
instead.

The user will describe what they want across multiple messages. Use the \
ask_user and confirm_action tools to clarify requirements and get approval \
before writing files or running simulations."""


@dataclass
class MultiTurnConfig:
    """Configuration for a multi-turn experiment run."""

    agent_model: str = "moonshotai/kimi-k2.5"
    simulator_model: str = "anthropic/claude-sonnet-4"
    max_agent_steps: int = 100  # Max tool-call iterations per step() call
    max_total_turns: int = 15  # Max user turns (initial + follow-ups)
    max_simulator_turns: int = 10  # Simulator's own turn budget
    max_resume_cycles: int = 20  # Max ask_user/confirm cycles per step
    agent_temperature: float = 0.2
    simulator_temperature: float = 0.4
    eval_preamble: Optional[str] = None  # Prepended to initial instruction


@dataclass
class TurnRecord:
    """Record of a single conversational turn."""

    turn_number: int
    turn_type: str  # "initial", "answer", "confirmation", "followup"
    user_message: str
    agent_question: Optional[str] = None  # Question that triggered an answer
    agent_response: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Colors for terminal output
# ---------------------------------------------------------------------------

class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


# ---------------------------------------------------------------------------
# Multi-turn experiment runner
# ---------------------------------------------------------------------------

class MultiTurnExperimentRunner:
    """Runs a single multi-turn experiment.

    Creates a GeosAgent in interactive mode and a UserSimulator, then
    orchestrates their conversation until the simulator signals completion
    or limits are reached.
    """

    def __init__(
        self,
        experiment_dir: Path,
        config: Optional[MultiTurnConfig] = None,
    ):
        self.experiment_dir = Path(experiment_dir).resolve()
        self.config = config or MultiTurnConfig()
        self.turns: List[TurnRecord] = []
        self.total_duration: float = 0.0

        # Read the full task specification
        instructions_path = self.experiment_dir / "instructions.txt"
        if not instructions_path.exists():
            raise FileNotFoundError(
                f"instructions.txt not found in {self.experiment_dir}"
            )
        self.task_spec = instructions_path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _make_stream_callback():
        """Create a minimal stream_callback to enable non-blocking IO tools.

        Setting any non-None stream_callback on GeosAgent causes AskUser
        and ConfirmAction tools to have ``blocking=False``, which makes
        them raise ``UserInputRequired`` instead of calling ``input()``.
        """
        def callback(event_type: str, data: Any) -> None:
            pass
        return callback

    def _build_conversation_summary(self) -> str:
        """Build a summary of the conversation so far for the simulator."""
        parts = []
        for turn in self.turns:
            label = f"Turn {turn.turn_number} ({turn.turn_type})"
            if turn.agent_question:
                parts.append(f"{label}:")
                parts.append(f"  Agent asked: {turn.agent_question[:300]}")
                parts.append(f"  User answered: {turn.user_message[:300]}")
            else:
                parts.append(f"{label}:")
                parts.append(f"  User: {turn.user_message[:300]}")
                if turn.agent_response:
                    parts.append(f"  Agent: {turn.agent_response[:300]}")
        return "\n".join(parts)

    def run(self) -> Dict[str, Any]:
        """Execute the full multi-turn experiment.

        Returns:
            Dictionary with experiment results, turn records, conversation
            log, and timing information.
        """
        # Lazy imports to avoid loading heavy dependencies at module level
        from geos_agent.agent_config import AgentConfig
        from geos_agent.geos_agent import AgentTerminationException, GeosAgent
        from geos_agent.tools.user_io import UserInputRequired
        from geos_agent.tools.utils import build_default_tools

        experiment_name = self.experiment_dir.name

        print(
            f"{Colors.OKCYAN}{Colors.BOLD}▶ Starting multi-turn experiment: "
            f"{experiment_name}{Colors.ENDC}"
        )

        # ---- Initialize simulator ----
        simulator = UserSimulator(
            task_specification=self.task_spec,
            config=SimulatorConfig(
                model=self.config.simulator_model,
                temperature=self.config.simulator_temperature,
                max_user_turns=self.config.max_simulator_turns,
            ),
        )

        # ---- Initialize agent (interactive mode, non-blocking IO) ----
        tools = build_default_tools(self.experiment_dir)
        agent_config = AgentConfig(
            model=self.config.agent_model,
            temperature=self.config.agent_temperature,
            max_steps=self.config.max_agent_steps,
            mode="interactive",
        )
        agent = GeosAgent(
            workspace_root=self.experiment_dir,
            tools=tools,
            config=agent_config,
            stream_callback=self._make_stream_callback(),
        )
        agent.start_session()

        # ---- Phase 1: Generate and send initial instruction ----
        print(f"  Generating initial instruction...", file=sys.stderr)
        initial_instruction = simulator.generate_initial_instruction()

        # Optionally prepend eval preamble
        preamble = self.config.eval_preamble or DEFAULT_EVAL_PREAMBLE
        if preamble:
            initial_instruction = preamble.strip() + "\n\n" + initial_instruction

        turn_num = 1
        terminated = False

        self._run_agent_turn(
            agent=agent,
            simulator=simulator,
            user_message=initial_instruction,
            turn_number=turn_num,
            turn_type="initial",
            UserInputRequired=UserInputRequired,
            AgentTerminationException=AgentTerminationException,
        )

        # Check if agent terminated on the initial turn
        if self.turns and self.turns[-1].error:
            terminated = True

        # ---- Phase 2: Follow-up loop ----
        turn_num += 1
        while not terminated and turn_num <= self.config.max_total_turns:
            summary = self._build_conversation_summary()
            followup = simulator.generate_followup(summary)

            if followup is None:
                print(
                    f"  {Colors.OKGREEN}Simulator signaled [TASK_COMPLETE] "
                    f"after {turn_num - 1} turns{Colors.ENDC}",
                    file=sys.stderr,
                )
                break

            print(
                f"  Follow-up turn {turn_num}...",
                file=sys.stderr,
            )

            self._run_agent_turn(
                agent=agent,
                simulator=simulator,
                user_message=followup,
                turn_number=turn_num,
                turn_type="followup",
                UserInputRequired=UserInputRequired,
                AgentTerminationException=AgentTerminationException,
            )

            # Check if agent terminated
            last_primary = next(
                (t for t in reversed(self.turns)
                 if t.turn_type in ("initial", "followup")),
                None,
            )
            if last_primary and last_primary.error:
                terminated = True

            turn_num += 1

        # ---- Collect results ----
        conversation_log = agent._get_conversation_log()

        user_turn_count = sum(
            1 for t in self.turns if t.turn_type in ("initial", "followup")
        )
        question_count = sum(
            1 for t in self.turns if t.turn_type in ("answer", "confirmation")
        )

        result = {
            "experiment": experiment_name,
            "mode": "multi_turn",
            "simulator_model": self.config.simulator_model,
            "agent_model": self.config.agent_model,
            "total_user_turns": user_turn_count,
            "total_agent_questions": question_count,
            "total_turns": len(self.turns),
            "total_duration_seconds": self.total_duration,
            "simulator_task_complete": simulator.task_complete,
            "agent_terminated": terminated,
            "turns": [self._turn_to_dict(t) for t in self.turns],
            "conversation_log": conversation_log,
        }

        status = (
            f"{Colors.OKGREEN}✓ Completed"
            if not terminated
            else f"{Colors.WARNING}⚠ Terminated"
        )
        print(
            f"  {status}: {experiment_name} "
            f"({self.total_duration:.1f}s, {user_turn_count} user turns, "
            f"{question_count} agent questions){Colors.ENDC}"
        )

        return result

    def _run_agent_turn(
        self,
        agent: Any,
        simulator: UserSimulator,
        user_message: str,
        turn_number: int,
        turn_type: str,
        UserInputRequired: type,
        AgentTerminationException: type,
    ) -> None:
        """Run a single agent turn, handling UserInputRequired cycles.

        A single "turn" from the user's perspective may involve multiple
        ask_user/confirm_action question-answer cycles internally.
        """
        start_time = time.monotonic()
        resume_cycles = 0
        agent_response = None
        error = None

        try:
            agent_response = agent.step(user_message)
        except UserInputRequired as e:
            # Agent is asking a question — enter the ask/answer loop
            while resume_cycles < self.config.max_resume_cycles:
                resume_cycles += 1
                question = e.question
                is_confirmation = getattr(e, "tool_name", "") == "confirm_action"

                # Get answer from the simulator
                answer = simulator.answer_question(
                    question=question,
                    choices=getattr(e, "choices", None),
                    is_confirmation=is_confirmation,
                )

                # Record the Q&A sub-turn
                qa_type = "confirmation" if is_confirmation else "answer"
                self.turns.append(TurnRecord(
                    turn_number=turn_number,
                    turn_type=qa_type,
                    user_message=answer,
                    agent_question=question,
                ))

                print(
                    f"    Agent asked ({qa_type}): "
                    f"{question[:80]}{'...' if len(question) > 80 else ''}",
                    file=sys.stderr,
                )

                try:
                    agent_response = agent.resume_after_user_input(answer)
                    break  # Agent finished this turn
                except UserInputRequired as e2:
                    e = e2  # Another question — loop again
                    continue

            else:
                # max_resume_cycles exceeded
                error = (
                    f"Agent asked {self.config.max_resume_cycles} questions "
                    f"in a single turn (max_resume_cycles exceeded)"
                )

        except AgentTerminationException as ate:
            error = str(ate)
            agent_response = getattr(ate, "last_assistant_message", None)

        except Exception as exc:
            error = f"Unexpected error: {type(exc).__name__}: {exc}"

        duration = time.monotonic() - start_time
        self.total_duration += duration

        # Record the primary turn (initial or followup)
        self.turns.append(TurnRecord(
            turn_number=turn_number,
            turn_type=turn_type,
            user_message=user_message,
            agent_response=agent_response,
            duration_seconds=duration,
            error=error,
        ))

    @staticmethod
    def _turn_to_dict(turn: TurnRecord) -> Dict[str, Any]:
        """Convert a TurnRecord to a JSON-serializable dictionary."""
        return {
            "turn_number": turn.turn_number,
            "turn_type": turn.turn_type,
            "user_message": turn.user_message,
            "agent_question": turn.agent_question,
            "agent_response": turn.agent_response,
            "duration_seconds": turn.duration_seconds,
            "error": turn.error,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    """Get project root directory."""
    return (Path(__file__).parent / "../..").resolve()


def main():
    parser = argparse.ArgumentParser(
        description="Run a single multi-turn GEOS agent evaluation experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--experiment-dir",
        type=Path,
        required=True,
        help="Path to experiment directory (must contain instructions.txt)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Directory to save logs (default: data/eval/multiturn_logs)",
    )
    parser.add_argument(
        "--agent-model",
        type=str,
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model for the GEOS agent (default: moonshotai/kimi-k2.5)",
    )
    parser.add_argument(
        "--simulator-model",
        type=str,
        default="anthropic/claude-sonnet-4",
        help="OpenRouter model for the user simulator (default: anthropic/claude-sonnet-4)",
    )
    parser.add_argument(
        "--max-agent-steps",
        type=int,
        default=100,
        help="Max tool-call iterations per agent step() call (default: 100)",
    )
    parser.add_argument(
        "--max-total-turns",
        type=int,
        default=15,
        help="Max user turns including initial + follow-ups (default: 15)",
    )
    parser.add_argument(
        "--max-simulator-turns",
        type=int,
        default=10,
        help="Max turns the simulator will produce (default: 10)",
    )
    parser.add_argument(
        "--no-eval-preamble",
        action="store_true",
        help="Disable the default eval preamble prepended to the initial instruction",
    )

    args = parser.parse_args()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Resolve paths
    experiment_dir = args.experiment_dir.resolve()
    project_root = get_project_root()
    log_dir = (args.log_dir or project_root / "data/eval/multiturn_logs").resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    experiment_name = experiment_dir.name

    # Build config
    config = MultiTurnConfig(
        agent_model=args.agent_model,
        simulator_model=args.simulator_model,
        max_agent_steps=args.max_agent_steps,
        max_total_turns=args.max_total_turns,
        max_simulator_turns=args.max_simulator_turns,
        eval_preamble=None if args.no_eval_preamble else DEFAULT_EVAL_PREAMBLE,
    )

    # Run the experiment
    runner = MultiTurnExperimentRunner(experiment_dir, config)
    result = runner.run()

    # Save multi-turn log
    multiturn_log_path = log_dir / f"{experiment_name}_multiturn.json"
    with open(multiturn_log_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nMulti-turn log saved to: {multiturn_log_path}")

    # Save standard conversation log (compatible with batch_evaluate.py)
    jsonl_log_path = log_dir / f"{experiment_name}.jsonl"
    with open(jsonl_log_path, "w", encoding="utf-8") as f:
        json.dump(result["conversation_log"], f, indent=2, ensure_ascii=False)
    print(f"Conversation log saved to: {jsonl_log_path}")


if __name__ == "__main__":
    main()
