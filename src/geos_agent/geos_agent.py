import json
import os
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
    Single-agent loop using OpenRouter's Chat Completions API.
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
        """Call OpenRouter Chat Completions API."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=self.messages,
            tools=self._get_tool_specs(),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response

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

    def run(self, user_input: str) -> str:
        """
        Run a full agent loop using Chat Completions API.
        """
        self._log("user_input", content=user_input)

        # Initialize messages with system prompt and user input
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]

        for step in range(1, self.config.max_steps + 1):
            self._log("step_start", step=step)
            
            response = self._call_model()
            message = response.choices[0].message
            
            # Add assistant message to history
            self.messages.append(message.model_dump())

            assistant_text = message.content or ""
            tool_calls = message.tool_calls or []

            self._log(
                "model_reply",
                step=step,
                content_preview=assistant_text[:200] if assistant_text else "",
                tools_requested=[tc.function.name for tc in tool_calls],
            )

            if not tool_calls:
                # No tools to run, we are done.
                self._log("run_complete", step=step, outcome="no_tool_calls")
                return assistant_text

            # Execute tools and add results to messages
            for tc in tool_calls:
                tool_message = self._run_tool_call(tc)
                self.messages.append(tool_message)

        self._log("max_steps_reached", max_steps=self.config.max_steps)
        
        # Return the last assistant message content
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]
        
        return ""
