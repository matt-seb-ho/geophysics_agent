import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from geos_agent.agent_config import AgentConfig
from geos_agent.tools.base import Tool

# ==============================
# Agent implementation
# ==============================


class GeosAgent:
    """
    Single-agent loop, inspired by Leonie Monigatti's 'AI agent from scratch' tutorial.
    - Maintains conversation history (short-term memory)
    - Uses OpenAI function calling (tools)
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
        self.client = OpenAI()
        self.config = config or AgentConfig()
        self.system_prompt = (
            "You are GEOS-Agent, an expert assistant for the GEOS / GEOSX software.\n"
            "- You can inspect and edit files in the workspace.\n"
            "- You can run shell commands and short Python snippets.\n"
            "- For now, GEOS itself and documentation search are partially stubbed; "
            "if a tool response says it's a stub, explain what *should* happen and "
            "suggest concrete next steps.\n"
            "- Prefer small, incremental changes to files rather than massive rewrites.\n"
            "- Always explain what you are doing and why, especially before running "
            "any shell commands.\n"
            "- Treat all paths as relative to the workspace root unless explicitly "
            "told otherwise."
        )

        self.messages: List[Dict[str, Any]] = []
        self.tools = tools
        self.tool_map = {t.name: t for t in tools}
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

    def _call_model(self) -> Any:
        """Call the OpenAI chat completion API with current messages."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=self.messages,
            tools=self._get_tool_specs(),
            tool_choice="auto",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response

    def _run_tool_call(self, tool_call) -> str:
        """Execute a single tool call and return a JSON-serializable result string."""
        name = tool_call.function.name
        args_str = tool_call.function.arguments or "{}"

        try:
            args = json.loads(args_str)
        except json.JSONDecodeError as e:
            result = {"error": f"Failed to parse tool arguments: {e}", "raw": args_str}
            self._log("tool_args_parse_error", tool=name, error=str(e), raw=args_str)
            return json.dumps(result, ensure_ascii=False)

        tool = self.tool_map.get(name)
        if tool is None:
            result = {"error": f"Unknown tool: {name}", "args": args}
            self._log("tool_unknown", tool=name, args=args)
            return json.dumps(result, ensure_ascii=False)

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
            return result_str
        except Exception as e:
            result = {"error": f"Tool {name} raised an exception: {e!r}", "args": args}
            self._log("tool_run_exception", tool=name, args=args, error=str(e))
            return json.dumps(result, ensure_ascii=False)

    # ------------- public API -------------

    def run(self, user_input: str) -> str:
        """
        Run a full agent loop for a single high-level user instruction.

        Returns the final assistant message content (string).
        """

        # Reset short-term memory for each top-level run.
        self.messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        self.messages.append({"role": "user", "content": user_input})
        self._log("user_input", content=user_input)

        for step in range(1, self.config.max_steps + 1):
            self._log("step_start", step=step)

            response = self._call_model()
            msg = response.choices[0].message

            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": msg.content or "",
            }

            # Attach tool_calls if present so the model sees them in history.
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            self.messages.append(assistant_msg)

            self._log(
                "model_reply",
                step=step,
                content_preview=(msg.content or "")[:200],
                tools_requested=[tc.function.name for tc in (msg.tool_calls or [])],
            )

            # If there are no tool calls, we treat this as the final answer.
            if not msg.tool_calls:
                final_text = msg.content or ""
                self._log("run_complete", step=step, outcome="no_tool_calls")
                return final_text

            # Otherwise, run each tool and feed back results.
            for tc in msg.tool_calls:
                result_str = self._run_tool_call(tc)

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    }
                )

        # If we hit max_steps without a natural stopping point, return last content.
        self._log("max_steps_reached", max_steps=self.config.max_steps)
        last_assistant = next(
            (m for m in reversed(self.messages) if m["role"] == "assistant"),
            None,
        )
        return (last_assistant or {}).get("content", "")
