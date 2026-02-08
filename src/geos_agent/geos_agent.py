import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from geos_agent.agent_config import AgentConfig
from geos_agent.tools.base import Tool

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
        log_path: Optional[Path] = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()

        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )
        self.config = config or AgentConfig()
        self.config.mode = (self.config.mode or "auto").lower()

        # base = (
        # "You are GEOS-Agent, an expert assistant for GEOS / GEOSX.\n"
        # "- Prefer small, incremental changes.\n"
        # "- Explain before running commands.\n"
        # )
        base = (
            "You are GEOS-Agent, an expert assistant for the GEOS / GEOSX software.\n"
            f"- Your workspace is: {self.workspace_root}\n"
            "- You can inspect files anywhere in the workspace (including instructions.txt).\n"
            "- You can run shell commands and short Python snippets within the workspace.\n"
            "- **CRITICAL FILE LOCATION RULES**:\n"
            "  1. ALL input XML files MUST be written to the `inputs/` directory\n"
            "  2. ALL simulation outputs MUST be written to the `outputs/` directory\n"
            "  3. NEVER write files to the workspace root or any other location\n"
            "  4. When using write_file, the path MUST start with 'inputs/' or 'outputs/'\n"
            "  5. Example: write_file path='inputs/simulation.xml' (CORRECT)\n"
            "  6. Example: write_file path='outputs/results.txt' (CORRECT)\n"
            "  7. Example: write_file path='simulation.xml' (INCORRECT - will be rejected)\n"
            "- **WORKFLOW: AFTER CREATING INPUT FILES, YOU MUST RUN THE SIMULATION**:\n"
            "  1. Once all XML input files are created in inputs/, use run_geos tool\n"
            "  2. Example: run_geos(input_path='inputs/triaxialDriver_ViscoDruckerPrager.xml')\n"
            "  3. If the simulation fails, analyze the error and fix the XML files\n"
            "  4. Re-run the simulation after fixes until it succeeds or outputs are generated\n"
            "  5. Check outputs/ directory for simulation results\n"
            "- For now, GEOS itself and documentation search are partially stubbed; "
            "if a tool response says it's a stub, explain what *should* happen and "
            "suggest concrete next steps.\n"
            "- Prefer small, incremental changes to files rather than massive rewrites.\n"
            "- Always explain what you are doing and why, especially before running "
            "any shell commands.\n"
            "- After creating or modifying files, summarize the key changes you made "
            "and explain the structure of what was generated."
        )
        if self.config.mode == "interactive":
            base += (
                "- You may ask clarifying questions using the ask_user tool.\n"
                "- Before writing files or running shell commands, use confirm_action.\n"
            )
        else:
            base += (
                "- Do NOT ask the user questions via tools.\n"
                "- If info is missing, make reasonable assumptions and state them.\n"
                "- If assumptions would be risky, output a short list of required inputs.\n"
            )
        self.system_prompt = base

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
        self.log_path = log_path

    # ------------- logging -------------

    def _log(self, event: str, **kwargs: Any) -> None:
        if not self.log_path:
            return
        record = {"event": event, **kwargs}
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            # Logging should never crash the agent
            pass

    # ------------- tool plumbing -------------

    def _get_tool_specs(self) -> List[Dict[str, Any]]:
        return [t.get_spec() for t in self.tools]

    def _call_model_streaming(self) -> tuple[str, List[Any]]:
        """Call OpenRouter Chat Completions API with streaming."""
        # Build extra body for reasoning models
        extra_body = {}
        if self.config.reasoning:
            extra_body["reasoning"] = {"enabled": True}

        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=self.messages,
            tools=self._get_tool_specs(),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
            extra_body=extra_body if extra_body else None,
            tool_choice="auto",
        )

        # Accumulate the response
        full_content = ""
        tool_calls_data: Dict[
            int, Dict[str, Any]
        ] = {}  # index -> {id, name, arguments}

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Handle text content
            if delta.content:
                print(delta.content, end="", flush=True)
                full_content += delta.content

            # Handle tool calls (they come in chunks)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_data:
                        tool_calls_data[idx] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc.id:
                        tool_calls_data[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_data[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_data[idx]["arguments"] += tc.function.arguments

        # Convert accumulated tool calls to a list
        tool_calls = []
        for idx in sorted(tool_calls_data.keys()):
            tc_data = tool_calls_data[idx]
            # Create a simple object-like structure
            tool_calls.append(
                type(
                    "ToolCall",
                    (),
                    {
                        "id": tc_data["id"],
                        "function": type(
                            "Function",
                            (),
                            {
                                "name": tc_data["name"],
                                "arguments": tc_data["arguments"],
                            },
                        )(),
                    },
                )()
            )

        if full_content:
            print()  # Newline after streaming

        return full_content, tool_calls

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

        print(f"[Running tool: {name}]", file=sys.stderr)

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

        # Task is considered complete if score > 0.3
        indicators["task_complete"] = indicators["completion_score"] > 0.3

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
