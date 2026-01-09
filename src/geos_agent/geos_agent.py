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

    def _call_model(
        self,
        input_item: Any,
        previous_response_id: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> Any:
        """Call the OpenAI responses API."""
        kwargs = {
            "model": self.config.model,
            "input": input_item,
            "tools": self._get_tool_specs(),
        }
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        if instructions:
            kwargs["instructions"] = instructions

        # v1/responses parameters (checking compatibility)
        if hasattr(self.config, "temperature"):
             pass
        
        # **api call**
        response = self.client.responses.create(**kwargs)
        return response

    def _run_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call and return a result item for v1/responses."""
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
            # Return a tool output item
            return {
                "type": "function_call", 
                "call_id": tool_call.call_id, 
                "output": result_str
            }

        tool = self.tool_map.get(name)
        if tool is None:
            result_str = json.dumps(
                {"error": f"Unknown tool: {name}", "args": args}, ensure_ascii=False
            )
            self._log("tool_unknown", tool=name, args=args)
            return {
                "call_id": tool_call.call_id,
                "type": "function_call",
                "output": result_str
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
                "call_id": tool_call.call_id,
                "type": "function_call",
                "output": result_str
            }
        except Exception as e:
            result_str = json.dumps(
                {"error": f"Tool {name} raised an exception: {e!r}", "args": args},
                ensure_ascii=False,
            )
            self._log("tool_run_exception", tool=name, args=args, error=str(e))
            return {
                "call_id": tool_call.call_id,
                "type": "function_call",
                "output": result_str
            }

    # ------------- public API -------------

    def run(self, user_input: str) -> str:
        """
        Run a full agent loop utilizing the v1/responses API.
        """
        self._log("user_input", content=user_input)

        # Initial request
        # For v1/responses, we send the user input and instructions.
        current_response = self._call_model(
            input_item=user_input,
            instructions=self.system_prompt,
        )

        for step in range(1, self.config.max_steps + 1):
            self._log("step_start", step=step, response_id=current_response.id)            
            assistant_text = ""
            tool_calls = []

            for item in current_response.output:
                if item.type == "message":
                    # content is a list of content blocks
                    if item.content:
                        for block in item.content:
                            if hasattr(block, 'text'):
                                assistant_text += block.text
                elif item.type == "function_call":
                    tool_calls.append(item)

            self._log(
                "model_reply",
                step=step,
                content_preview=assistant_text[:200],
                tools_requested=[tc.function.name for tc in tool_calls],
            )

            if not tool_calls:
                # No tools to run, we are done.
                self._log("run_complete", step=step, outcome="no_tool_calls")
                return assistant_text

            # Execute tools
            tool_outputs = []
            for tc in tool_calls:
                output_item = self._run_tool_call(tc)
                tool_outputs.append(output_item)

            # Feed back to model
            current_response = self._call_model(
                input_item=tool_outputs,
                previous_response_id=current_response.id
            )

        self._log("max_steps_reached", max_steps=self.config.max_steps)
        # Try to extract text from the last response
        final_text = ""
        for item in current_response.output:
            if item.type == "message":
                if item.content:
                    for block in item.content:
                        if hasattr(block, 'text'):
                            final_text += block.text
                
        return final_text
