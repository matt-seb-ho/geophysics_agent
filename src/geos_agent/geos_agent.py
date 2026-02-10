import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from geos_agent.agent_config import AgentConfig
from geos_agent.api_client import OpenRouterClient, RetryConfig
from geos_agent.tools.base import Tool

# ==============================
# System Prompt Template
# ==============================

SYSTEM_PROMPT_TEMPLATE = """\
You are GEOS Expert, an assistant for the GEOS multiphysics simulator (GEOS/GEOSX). \
Your job is to turn a geoscientist's natural-language modeling intent into an \
end-to-end GEOS workflow: design the physics setup, create/modify GEOS XML input \
decks, run simulations, diagnose failures, and suggest post-processing steps \
(visualization, data extraction).


Your workspace: {workspace_root}


PRIMARY RESPONSIBILITY: Input deck authoring. Given a user's scenario (domain, \
geometry/mesh, materials, initial/boundary conditions, physics couplings, outputs), \
you either (1) fully specify the needed XML files yourself, or (2) ask targeted \
questions to fill missing fields. Prefer minimal, working examples first, then iterate.


INPUT FILE ORGANIZATION (Base/Benchmark Pattern):
When creating GEOS input files, PREFER the two-file pattern used in validation examples:
  • `*_base.xml` — Core physics setup: mesh definition, solver configurations, \
    constitutive laws, boundary condition types, and general physics structure. \
    This file should be reusable across multiple runs.
  • `*_benchmark.xml` (or other appropriate suffix like `_run`, `_case`, `_scenario`) — \
    Case-specific parameters: material property values, injection rates, simulation \
    times, and other scenario-specific settings. Include via <Included> tag in the base \
    file or run separately.

This pattern promotes reusability and parameter sweeps. If the scenario is simple \
with no anticipated variants, a single file is acceptable. Use suffixes that match \
the context (e.g., `_base` and `_run` for execution variants, `_base` and `_benchmark` \
for validation, `_base` and `_case1` for multiple scenarios).


VISUALIZATION SCRIPT GENERATION:
ALWAYS generate Python visualization scripts alongside input files when applicable:
  • Create scripts in `inputs/scripts/` directory (e.g., `inputs/scripts/plot_results.py`)
  • Scripts should read GEOS outputs from `outputs/` directory (HDF5, VTK, or text files)
  • Include functions to plot key quantities: pressure vs time, fracture dimensions, \
    stress distributions, etc.
  • Follow GEOS conventions: use `matplotlib` for static plots, provide save/show options
  • Reference the hydrofracture example pattern: queries script for data extraction, \
    figure script for publication-quality plots


WORKFLOW DISCIPLINE:
1. Determine the required physics setup (solvers, mesh, materials, BCs, couplings, outputs)
2. If critical specs are missing, ask targeted questions (interactive) or make stated assumptions (auto)
3. Generate/patch XML files following file location rules below
4. Run GEOS, inspect logs/output, and refine as needed
5. Provide post-processing steps (scripts/commands) to extract key quantities or visualize


CRITICAL FILE LOCATION RULES:
  • ALL files that you write (including XML files) → `inputs/` directory
  • ALL simulation outputs and outputs from scripts you run → `outputs/` directory
  • Visualization scripts → `inputs/scripts/` directory
  • NEVER write files to workspace root or other locations
  • When using write_file: path MUST start with 'inputs/' or 'outputs/'
  • Examples: 'inputs/simulation_base.xml' ✓  'inputs/myCase_benchmark.xml' ✓  \
    'inputs/scripts/plot_fracture.py' ✓  'outputs/results.txt' ✓  'simulation.xml' ✗


EXECUTION REQUIREMENTS:
  • After creating XML in inputs/, ALWAYS run the simulation using run_geos tool
  • If simulation fails, analyze errors and fix XML
  • Re-run until success or outputs are generated
  • Check outputs/ directory for results


POST-PROCESSING REQUIREMENTS:
  • After successful simulation, run or provide visualization scripts
  • Generated plots should be saved to `outputs/` directory
  • Summarize key results (fracture dimensions, pressures, etc.) in your response


SAFETY & CORRECTNESS:
  • Never invent GEOS XML schema details—verify against docs when unsure
  • For expensive runs, suggest smaller sanity checks first (coarser mesh, fewer timesteps)
  • Always explain what you are doing and why before running commands
  • After creating/modifying files, summarize key changes and structure
  • Prefer small, incremental changes over massive rewrites


TOOLS AVAILABLE:
  • Search tools: query GEOS documentation (conceptual + technical/XML syntax)
  • File tools: read, write, list (restricted to workspace)
  • Shell tools: run commands, execute Python snippets
  • Code retrieval: fetch actual XML examples from docs
  • GEOS execution: run simulations with run_geos tool
{mode_specific}
{primer}"""


MODE_INTERACTIVE = """

INTERACTION MODE: Interactive
  • You may ask clarifying questions using ask_user tool
  • Before writing files or running commands, use confirm_action
  • Prefer asking over guessing when specs are unclear"""

MODE_AUTO = """

INTERACTION MODE: Autonomous
  • Do NOT ask user questions via tools—make decisions autonomously
  • If info is missing, make reasonable assumptions and clearly state them
  • If assumptions would be risky, provide a short list of what's needed but proceed anyway"""

PRIMER_TEMPLATE = """
{separator}
GEOS PRIMER - Quick Reference
{separator}

{content}

{separator}
END OF GEOS PRIMER
{separator}"""

# ==============================
# Exceptions
# ==============================


class AgentTerminationException(Exception):
    """Exception raised when the agent terminates prematurely or unexpectedly."""

    def __init__(
        self,
        message: str,
        reason: str,
        step_count: int,
        max_steps: int,
        last_assistant_message: Optional[str] = None,
        tool_calls_made: int = 0,
        diagnostic_info: Optional[Dict[str, Any]] = None,
    ):
        self.reason = reason
        self.step_count = step_count
        self.max_steps = max_steps
        self.last_assistant_message = last_assistant_message
        self.tool_calls_made = tool_calls_made
        self.diagnostic_info = diagnostic_info or {}

        # Build detailed error message
        full_message = f"{message}\n\n"
        full_message += f"Termination Reason: {reason}\n"
        full_message += f"Steps Executed: {step_count}/{max_steps}\n"
        full_message += f"Tool Calls Made: {tool_calls_made}\n"

        if last_assistant_message:
            preview = (
                last_assistant_message[:200] + "..."
                if len(last_assistant_message) > 200
                else last_assistant_message
            )
            full_message += f"\nLast Assistant Message:\n{preview}\n"

        if diagnostic_info:
            full_message += "\nDiagnostic Information:\n"
            for key, value in diagnostic_info.items():
                full_message += f"  {key}: {value}\n"

        super().__init__(full_message)


# ==============================
# Agent implementation
# ==============================


class GeosAgent:
    """
    Single-agent loop using OpenRouter's Chat Completions API with streaming.
    - Maintains conversation history (short-term memory)
    - Uses function calling (tools)
    - Runs tools in a loop until no tool calls are requested
    """

    def __init__(
        self,
        workspace_root: Path,
        tools: List[Tool],
        config: Optional[AgentConfig] = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()

        # Initialize OpenRouter client with retry configuration
        retry_config = RetryConfig(
            max_retries=config.max_retries if config else 3,
            retry_delay=config.retry_delay if config else 1.0,
            retry_backoff=config.retry_backoff if config else 2.0,
            retry_on_timeout=config.retry_on_timeout if config else True,
            retry_on_rate_limit=config.retry_on_rate_limit if config else True,
            retry_on_server_error=config.retry_on_server_error if config else True,
        )
        self.client = OpenRouterClient(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            retry_config=retry_config,
            log_callback=self._log,
        )
        self.config = config or AgentConfig()
        self.config.mode = (self.config.mode or "auto").lower()

        # Build mode-specific instructions
        mode_specific = MODE_INTERACTIVE if self.config.mode == "interactive" else MODE_AUTO

        # Build primer section if configured
        primer = ""
        if self.config.include_primer:
            from geos_agent.constants import PRIMER_PATH

            if PRIMER_PATH.exists():
                try:
                    primer_content = PRIMER_PATH.read_text(encoding="utf-8")
                    primer = PRIMER_TEMPLATE.format(
                        separator="=" * 80,
                        content=primer_content
                    )
                except Exception as e:
                    # If primer can't be loaded, log but don't fail
                    print(f"Warning: Could not load GEOS primer: {e}", file=sys.stderr)

        # Format the final system prompt
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            workspace_root=self.workspace_root,
            mode_specific=mode_specific,
            primer=primer
        )

        self.messages: List[Dict[str, Any]] = []
        # self.tools = tools
        if self.config.mode == "interactive":
            self.tools = tools
        else:
            # drop interactive tools in auto mode
            self.tools = [
                t for t in tools if t.name not in {"ask_user", "confirm_action"}
            ]

        self.tool_map = {t.name: t for t in self.tools}

    # ------------- logging -------------

    def _log(self, event: str, **kwargs: Any) -> None:
        # Legacy logging method kept for compatibility but no longer writes to file.
        # Structured logging is now handled by get_conversation_log()
        pass

    def get_conversation_log(self) -> Dict[str, Any]:
        """Generate a complete conversation log with user prompts, agent messages, and tool calls.
        
        Returns:
            Dictionary containing:
            - user_prompt: The initial user instruction
            - messages: List of all conversation messages
            - tool_calls: List of all tool calls with details
            - summary: High-level statistics
        """
        user_prompt = None
        agent_messages = []
        tool_calls_list = []
        tool_responses = []
        
        # Extract information from messages
        for msg in self.messages:
            role = msg.get("role")
            
            if role == "user":
                # Capture the user's prompt (typically the first user message)
                if user_prompt is None:
                    user_prompt = msg.get("content", "")
            
            elif role == "assistant":
                # Capture assistant messages and their tool calls
                agent_message = {
                    "content": msg.get("content", ""),
                    "tool_calls": []
                }
                
                # Extract tool calls if present
                if "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        tool_call_info = {
                            "id": tc.get("id"),
                            "tool_name": tc.get("function", {}).get("name"),
                            "arguments": tc.get("function", {}).get("arguments"),
                        }
                        agent_message["tool_calls"].append(tool_call_info)
                        tool_calls_list.append(tool_call_info)
                
                agent_messages.append(agent_message)
            
            elif role == "tool":
                # Capture tool responses
                tool_responses.append({
                    "tool_call_id": msg.get("tool_call_id"),
                    "content": msg.get("content", "")
                })
        
        # Build summary statistics
        summary = {
            "total_agent_messages": len(agent_messages),
            "total_tool_calls": len(tool_calls_list),
            "unique_tools_used": len(set(
                tc["tool_name"] for tc in tool_calls_list if tc["tool_name"]
            )),
        }
        
        return {
            "user_prompt": user_prompt,
            "agent_messages": agent_messages,
            "tool_calls": tool_calls_list,
            "tool_responses": tool_responses,
            "summary": summary,
            "all_messages": self.messages,
        }

    # ------------- tool plumbing -------------

    def _get_tool_specs(self) -> List[Dict[str, Any]]:
        return [t.get_spec() for t in self.tools]

    def _call_model_streaming(self) -> tuple[str, List[Any]]:
        """Call LLM with streaming. All API details handled by client."""
        return self.client.chat_completion_streaming(
            messages=self.messages,
            tools=self._get_tool_specs(),
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            reasoning=self.config.reasoning,
            tool_choice="auto",
        )


    def _run_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call and return a tool message."""
        name = tool_call.function.name
        args_str = tool_call.function.arguments or "{}"

        try:
            args = json.loads(args_str)
        except json.JSONDecodeError as e:
            result_str = json.dumps(
                {"error": f"Failed to parse tool arguments: {e}", "raw": args_str},
                ensure_ascii=False,
            )
            self._log("tool_args_parse_error", tool=name, error=str(e), raw=args_str)
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            }

        tool = self.tool_map.get(name)
        if tool is None:
            result_str = json.dumps(
                {"error": f"Unknown tool: {name}", "args": args}, ensure_ascii=False
            )
            self._log("tool_unknown", tool=name, args=args)
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            }

        # Get descriptive summary from the tool itself
        args_summary = tool.format_execution_summary(**args)
        print(f"\n🔧 {name}: {args_summary}", file=sys.stderr, flush=True)

        try:
            output_obj = tool.run(**args)
            if isinstance(output_obj, str):
                result_str = output_obj
            else:
                result_str = json.dumps(output_obj, ensure_ascii=False)
            self._log(
                "tool_run_ok",
                tool=name,
                args=args,
                result_preview=result_str[:500],
            )
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            }
        except Exception as e:
            result_str = json.dumps(
                {"error": f"Tool {name} raised an exception: {e!r}", "args": args},
                ensure_ascii=False,
            )
            self._log("tool_run_exception", tool=name, args=args, error=str(e))
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            }

    # ------------- public API -------------

    def start_session(self) -> None:
        """Start/clear a session, keeping the system prompt."""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def step(self, user_input: str) -> str:
        """One user turn + tool loop, appending to existing history.

        Raises:
            AgentTerminationException: If the agent terminates prematurely or
                reaches max_steps without completing the task.
        """
        if not self.messages:
            self.start_session()

        self._log("user_input", content=user_input)
        self.messages.append({"role": "user", "content": user_input})

        total_tool_calls = 0
        last_assistant_text = ""
        termination_reason = None
        diagnostic_info = {}

        for step_idx in range(1, self.config.max_steps + 1):
            self._log("step_start", step=step_idx)

            assistant_text, tool_calls = self._call_model_streaming()
            last_assistant_text = assistant_text

            assistant_message: Dict[str, Any] = {
                "role": "assistant",
                "content": assistant_text,
            }
            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            self.messages.append(assistant_message)

            tool_names = [tc.function.name for tc in tool_calls]
            self._log(
                "model_reply",
                step=step_idx,
                content_preview=(assistant_text or "")[:200],
                tools_requested=tool_names,
            )

            if not tool_calls:
                # Agent stopped requesting tools - check if this is premature
                termination_reason = "no_tool_calls"
                self._log("turn_complete", step=step_idx, outcome=termination_reason)

                # Check for indicators of incomplete task
                indicators = self._check_completion_indicators(assistant_text)
                diagnostic_info.update(indicators)

                # Raise exception if task appears incomplete
                if not indicators.get("task_complete", False):
                    raise AgentTerminationException(
                        message="Agent terminated without completing the task",
                        reason="Agent stopped requesting tools before task completion",
                        step_count=step_idx,
                        max_steps=self.config.max_steps,
                        last_assistant_message=assistant_text,
                        tool_calls_made=total_tool_calls,
                        diagnostic_info=diagnostic_info,
                    )

                return assistant_text

            # Execute tool calls
            for tc in tool_calls:
                tool_message = self._run_tool_call(tc)
                self.messages.append(tool_message)
                total_tool_calls += 1

        # Max steps reached
        termination_reason = "max_steps_reached"
        self._log("max_steps_reached", max_steps=self.config.max_steps)

        raise AgentTerminationException(
            message=f"Agent reached maximum step limit ({self.config.max_steps})",
            reason="Maximum number of steps exceeded",
            step_count=self.config.max_steps,
            max_steps=self.config.max_steps,
            last_assistant_message=last_assistant_text,
            tool_calls_made=total_tool_calls,
            diagnostic_info={
                "note": "Consider increasing max_steps in AgentConfig if task requires more iterations",
                "tool_call_rate": total_tool_calls / self.config.max_steps
                if self.config.max_steps > 0
                else 0,
            },
        )

    def _check_completion_indicators(self, text: str) -> Dict[str, Any]:
        """Check if the assistant's response indicates task completion.

        Returns a dictionary with completion indicators.
        """
        if not text:
            return {"task_complete": False, "reason": "Empty response"}

        text_lower = text.lower()

        # Indicators of task completion
        completion_phrases = [
            "successfully created",
            "file has been created",
            "completed",
            "finished",
            "done",
            "xml file is ready",
            "simulation is ready",
            "created successfully",
            "has been written",
            "successfully executed",
            "simulation has been",
            "results demonstrate",
            "output shows",
        ]

        # Indicators of incomplete task (asking for more info)
        incomplete_phrases = [
            "need more information",
            "please provide",
            "cannot proceed",
            "missing information",
            "i need to know",
            "could you clarify",
            "what would you like",
            "how would you like",
        ]

        # Check for error indicators
        error_indicators = [
            "error",
            "failed",
            "unable to",
            "could not",
            "permission denied",
        ]

        indicators = {
            "task_complete": False,
            "completion_score": 0.0,
            "detected_phrases": [],
        }

        # Check completion phrases
        for phrase in completion_phrases:
            if phrase in text_lower:
                indicators["completion_score"] += 0.2
                indicators["detected_phrases"].append(f"completion: {phrase}")

        # Check incomplete phrases (reduce score)
        for phrase in incomplete_phrases:
            if phrase in text_lower:
                indicators["completion_score"] -= 0.3
                indicators["detected_phrases"].append(f"incomplete: {phrase}")

        # Check error indicators
        error_count = sum(
            1 for indicator in error_indicators if indicator in text_lower
        )
        if error_count > 0:
            indicators["errors_detected"] = error_count
            indicators["completion_score"] -= 0.2 * error_count

        # Check for GEOS simulation success indicators
        # Look for evidence that simulation ran and produced outputs
        simulation_success_indicators = [
            "outputs/" in text_lower,  # Mentions output directory
            ".txt" in text_lower or ".csv" in text_lower,  # Mentions output files
            "simulation" in text_lower and ("run" in text_lower or "executed" in text_lower),
            "geos" in text_lower and "success" in text_lower,
        ]

        simulation_success_count = sum(1 for indicator in simulation_success_indicators if indicator)
        if simulation_success_count >= 2:
            indicators["completion_score"] += 0.3
            indicators["detected_phrases"].append("simulation_success: output file indicators found")

        # Check if outputs directory was mentioned with specific files
        if "outputs/" in text_lower and any(ext in text_lower for ext in [".txt", ".csv", ".hdf5", ".vtk"]):
            indicators["completion_score"] += 0.2
            indicators["detected_phrases"].append("completion: output files mentioned")

        # Task is considered complete if score > 0.15 (lowered from 0.3)
        # This allows a single completion phrase to succeed, but simulation
        # success indicators can also push it over the threshold
        indicators["task_complete"] = indicators["completion_score"] > 0.15

        return indicators

    def run(self, user_input: str) -> str:
        """Backwards compatible: one-shot session per call."""
        self.start_session()
        return self.step(user_input)

    def interactive_cli(self) -> None:
        """Simple REPL that keeps context and uses ask_user/confirm_action tools."""
        self.start_session()
        print("GEOS-Agent interactive session. Type 'exit' to quit.\n")
        while True:
            user_input = input("You> ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            _ = self.step(user_input)
            print()  # spacing
