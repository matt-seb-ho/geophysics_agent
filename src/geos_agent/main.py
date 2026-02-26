import sys
from pathlib import Path

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.utils import build_default_tools

# ==============================
# Simple CLI entrypoint
# ==============================


def _save_log(agent: GeosAgent, log_path: str) -> None:
    """Save the conversation log to a JSON file."""
    import json

    log_data = agent._get_conversation_log()
    log_file = Path(log_path).resolve()
    with log_file.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    print(f"\nConversation log saved to: {log_file}")


def _curate_cheatsheet(agent: GeosAgent, config: AgentConfig) -> None:
    """Run post-run cheatsheet curation if enabled."""
    if not config.curate_cheatsheet:
        return

    from geos_agent.cheatsheet import curate_and_save
    from geos_agent.constants import CHEATSHEET_PATH

    try:
        log_data = agent._get_conversation_log()
        curate_and_save(
            conversation_log=log_data,
            cheatsheet_path=CHEATSHEET_PATH,
            client=agent.client,
            model=config.curator_model or config.model,
        )
    except Exception as e:
        print(f"Warning: Cheatsheet curation failed: {e}", file=sys.stderr)


def main():
    import argparse

    from dotenv import load_dotenv

    load_dotenv()  # Load environment variables from .env if present

    parser = argparse.ArgumentParser(
        description="GEOS-Agent: minimal file/code agent scaffold for GEOS workflows."
    )
    parser.add_argument(
        "--instruction",
        type=str,
        help="High-level natural language instruction for the agent.",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Workspace root directory (default: current directory).",
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="Optional path to save the structured conversation log (JSON).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model name.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Maximum agent-tool iterations (default: 100).",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of API retry attempts (default: 3).",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Initial delay between retries in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Exponential backoff multiplier for retry delays (default: 2.0).",
    )
    parser.add_argument(
        "--no-cheatsheet",
        action="store_true",
        help="Disable dynamic cheatsheet loading and post-run curation.",
    )
    parser.add_argument(
        "--no-curate",
        action="store_true",
        help="Disable post-run cheatsheet curation (still loads existing cheatsheet).",
    )
    parser.add_argument(
        "--curator-model",
        type=str,
        default=None,
        help="Model to use for cheatsheet curation (default: same as --model).",
    )

    args = parser.parse_args()
    workspace_root = Path(args.workspace).resolve()

    tools = build_default_tools(workspace_root)
    config = AgentConfig(
        model=args.model,
        max_steps=args.max_steps,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        retry_backoff=args.retry_backoff,
        include_cheatsheet=not args.no_cheatsheet,
        curate_cheatsheet=not args.no_cheatsheet and not args.no_curate,
        curator_model=args.curator_model,
    )
    agent = GeosAgent(
        workspace_root=workspace_root,
        tools=tools,
        config=config,
    )

    if args.instruction is not None:
        instruction = args.instruction  # Already a string, no need to join
        print(f"=== GEOS-Agent (workspace: {workspace_root}) ===")
        print(f"Instruction: {instruction}")
        print("--------------------------------------------------")

        try:
            agent.run(instruction)

            if args.log:
                _save_log(agent, args.log)

            _curate_cheatsheet(agent, config)

        except AgentTerminationException as e:
            print("\n" + "=" * 60, file=sys.stderr)
            print("AGENT TERMINATION ERROR", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(str(e), file=sys.stderr)
            print("=" * 60, file=sys.stderr)

            if args.log:
                try:
                    _save_log(agent, args.log)
                except Exception as log_error:
                    print(f"Failed to save conversation log: {log_error}", file=sys.stderr)

            # Still curate on failure — errors are valuable learning
            _curate_cheatsheet(agent, config)

            sys.exit(1)
    else:
        print("GEOS-Agent interactive mode. Type 'exit' or 'quit' to exit.")
        try:
            agent.interactive_cli()
        except AgentTerminationException as e:
            print("\n" + "=" * 60, file=sys.stderr)
            print("AGENT TERMINATION ERROR", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(str(e), file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
