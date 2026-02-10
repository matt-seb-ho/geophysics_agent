import sys
from pathlib import Path

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.utils import build_default_tools

# ==============================
# Simple CLI entrypoint
# ==============================


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
        help="Optional JSONL log file path.",
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

    args = parser.parse_args()
    workspace_root = Path(args.workspace).resolve()
    log_path = Path(args.log) if args.log else None

    tools = build_default_tools(workspace_root)
    config = AgentConfig(
        model=args.model,
        max_steps=args.max_steps,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        retry_backoff=args.retry_backoff,
    )
    agent = GeosAgent(
        workspace_root=workspace_root,
        tools=tools,
        config=config,
        log_path=log_path,
    )

    if args.instruction is not None:
        instruction = args.instruction  # Already a string, no need to join
        print(f"=== GEOS-Agent (workspace: {workspace_root}) ===")
        print(f"Instruction: {instruction}")
        print("--------------------------------------------------")

        try:
            agent.run(instruction)
            
            # Save conversation log to log.json
            import json
            log_data = agent.get_conversation_log()
            log_file = workspace_root / "log.json"
            with log_file.open("w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            print(f"\nConversation log saved to: {log_file}")
            
        except AgentTerminationException as e:
            print("\n" + "=" * 60, file=sys.stderr)
            print("AGENT TERMINATION ERROR", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(str(e), file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            
            # Save conversation log even on error
            import json
            try:
                log_data = agent.get_conversation_log()
                log_file = workspace_root / "log.json"
                with log_file.open("w", encoding="utf-8") as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                print(f"\nConversation log saved to: {log_file}", file=sys.stderr)
            except Exception as log_error:
                print(f"Failed to save conversation log: {log_error}", file=sys.stderr)
            
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
