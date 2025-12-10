from pathlib import Path

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import GeosAgent
from geos_agent.tools.utils import build_default_tools

# ==============================
# Simple CLI entrypoint
# ==============================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="GEOS-Agent: minimal file/code agent scaffold for GEOS workflows."
    )
    parser.add_argument(
        "instruction",
        type=str,
        nargs="+",
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
        default="gpt-5.1-mini",
        help="OpenAI model name.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum agent-tool iterations.",
    )

    args = parser.parse_args()
    workspace_root = Path(args.workspace).resolve()
    log_path = Path(args.log) if args.log else None

    tools = build_default_tools(workspace_root)
    config = AgentConfig(model=args.model, max_steps=args.max_steps)
    agent = GeosAgent(
        workspace_root=workspace_root,
        tools=tools,
        config=config,
        log_path=log_path,
    )

    instruction = " ".join(args.instruction)
    print(f"=== GEOS-Agent (workspace: {workspace_root}) ===")
    print(f"Instruction: {instruction}")
    print("--------------------------------------------------")

    final_answer = agent.run(instruction)
    print("\n=== Final answer ===\n")
    print(final_answer)


if __name__ == "__main__":
    main()
