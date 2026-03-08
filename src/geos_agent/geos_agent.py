import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from geos_agent.agent_config import AgentConfig
from geos_agent.api_client import OpenRouterClient, RetryConfig
from geos_agent.constants import SYSTEM_PROMPT_PATH
from geos_agent.context_pruning import ContextPruningManager, strip_message_refs
from geos_agent.tools.base import Tool
from geos_agent.tools.user_io import UserInputRequired

# ==============================
# System Prompt Template
# ==============================

def _load_system_prompt_template() -> str:
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        print(
            f"Warning: Could not load system prompt template from {SYSTEM_PROMPT_PATH}: {exc}",
            file=sys.stderr,
        )
        return (
            "You are GEOS Expert.\n"
            "Your workspace: {workspace_root}\n"
            "{mode_specific}\n"
            "{primer}\n"
            "{cheatsheet}"
        )


SYSTEM_PROMPT_TEMPLATE = _load_system_prompt_template()


MODE_INTERACTIVE = """

INTERACTION MODE: Interactive — Human-in-the-Loop
  This session is INTERACTIVE. The user wants to collaborate, not just receive outputs.
  You MUST use the ask_user and confirm_action tools as described below.

  MANDATORY CHECKPOINTS (do NOT skip these):

  1. BEFORE writing ANY files: Use ask_user to present your plan.
     Summarize what files you will create, the key parameter values you intend
     to use, and the physics setup. Ask the user to confirm or adjust values.
     Even if you found an exact example in the documentation, the user may want
     different parameters — always check.

  2. BEFORE running simulations: Use confirm_action with a summary of what
     will be executed (input file path, expected runtime, what outputs to expect).

  3. AFTER simulation completes: Summarize results and use ask_user to ask
     what post-processing or visualization the user wants, rather than assuming.

  WHEN INFORMATION IS INCOMPLETE OR AMBIGUOUS:
  • Use ask_user to request missing values — do NOT guess or assume defaults.
  • If you find a matching example in the docs, present the example's parameter
    values to the user and ask which ones they want to keep vs. change.
  • Offer choices when possible (e.g., material models, mesh resolution, BCs).

  GENERAL RULES:
  • Prefer multiple short interactions over one long autonomous run.
  • Never write more than one batch of files without checking back with the user.
  • It is better to ask one too many questions than to produce unwanted output."""

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
        stream_callback: Optional[Callable] = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.stream_callback = stream_callback

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
            stream_callback=stream_callback,
        )
        self.config = config or AgentConfig()
        self.config.mode = (self.config.mode or "auto").lower()

        # Build mode-specific instructions
        mode_specific = MODE_INTERACTIVE if self.config.mode == "interactive" else MODE_AUTO

        # Import source directory constants for path resolution guidance
        from geos_agent.constants import GEOS_SOURCE_DIR, GEOSDATA_SOURCE_DIR

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

        # Build cheatsheet section if configured
        cheatsheet_section = ""
        if self.config.include_cheatsheet:
            from geos_agent.cheatsheet import CHEATSHEET_TEMPLATE, load_cheatsheet
            from geos_agent.constants import CHEATSHEET_PATH

            cheatsheet_content = load_cheatsheet(CHEATSHEET_PATH)
            if cheatsheet_content:
                cheatsheet_section = CHEATSHEET_TEMPLATE.format(
                    separator="=" * 80,
                    content=cheatsheet_content,
                )

        # Format the final system prompt
        self._context_pruning = ContextPruningManager(self.config)
        context_pruning_prompt = self._context_pruning.render_system_prompt()
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            workspace_root=self.workspace_root,
            mode_specific=mode_specific,
            primer=primer,
            cheatsheet=cheatsheet_section,
            geos_source_dir=GEOS_SOURCE_DIR,
            geosdata_source_dir=GEOSDATA_SOURCE_DIR,
        )
        if context_pruning_prompt:
            self.system_prompt = f"{self.system_prompt}\n{context_pruning_prompt}"

        self.messages: List[Dict[str, Any]] = []
        if self.config.mode == "interactive":
            self.tools = tools
        else:
            # drop interactive tools in auto mode
            self.tools = [
                t for t in tools if t.name not in {"ask_user", "confirm_action"}
            ]
        self.tools.extend(self._context_pruning.build_tools())

        self.tool_map = {t.name: t for t in self.tools}

        # When driven by a GUI (stream_callback set), make IO tools
        # non-blocking so they raise UserInputRequired instead of input().
        if stream_callback:
            for t in self.tools:
                if hasattr(t, "blocking"):
                    t.blocking = False

        self._pending_user_input: Optional[dict] = None
        self._last_projection_stats: Dict[str, Any] = {
            "enabled": bool(self.config.enable_context_projection),
            "active": False,
            "original_chars": 0,
            "projected_chars": 0,
            "messages_projected": 0,
        }
        self._last_pruning_stats: Dict[str, Any] = {
            "enabled": bool(self.config.context_pruning.enabled),
            "active": False,
            "pruned_tool_count": 0,
            "distilled_tool_count": 0,
            "compressed_block_count": 0,
            "saved_tokens_est": 0,
        }

    # ------------- logging -------------

    def _log(self, event: str, **kwargs: Any) -> None:
        # Legacy logging method kept for compatibility but no longer writes to file.
        # Structured logging is now handled by _get_conversation_log()
        pass

    def _get_conversation_log(self) -> Dict[str, Any]:
        """Generate a complete conversation log with user prompts, agent messages, and tool calls.
        
        Returns:
            Dictionary containing:
            - user_prompt: The initial user instruction
            - messages: List of all conversation messages
            - tool_calls: List of all tool calls with details
            - summary: High-level statistics
            - usage: Token usage statistics
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
            "usage": self.client.get_token_usage(),
            "context_projection": self._last_projection_stats,
            "context_pruning": self._last_pruning_stats,
        }

    # ------------- tool plumbing -------------

    def _get_tool_specs(self) -> List[Dict[str, Any]]:
        return [t.get_spec() for t in self.tools]

    @staticmethod
    def _safe_load_tool_arguments(arguments: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(arguments or "{}")
        except Exception:
            return {"_raw_arguments": arguments}
        return parsed if isinstance(parsed, dict) else {"_parsed_arguments": parsed}

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> str:
        """Truncate text while preserving a clear omission marker."""
        if not isinstance(text, str):
            text = str(text)
        if max_chars <= 0 or len(text) <= max_chars:
            return text
        omitted = len(text) - max_chars
        return f"{text[:max_chars]}\n...[truncated {omitted} chars]..."

    def _estimate_message_payload_chars(self, messages: List[Dict[str, Any]]) -> int:
        """Rough payload estimator for context projection decisions."""
        total = 0
        for msg in messages:
            total += len(msg.get("content", "") or "")
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {}) or {}
                total += len(fn.get("arguments", "") or "")
        return total

    def _estimate_message_payload_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count from payload size using a simple chars-per-token heuristic."""
        chars = self._estimate_message_payload_chars(messages)
        return max(0, (chars + 3) // 4)

    def _compact_data_for_context(self, value: Any, depth: int = 0) -> Any:
        """Recursively compact large tool payloads for model context."""
        max_depth = 4
        max_str = max(120, self.config.context_projection_max_string_chars)
        max_list = max(1, self.config.context_projection_max_list_items)
        max_dict_keys = 30

        heavy_string_keys = {
            "content",
            "spec",
            "shadow_text",
            "stdout",
            "stderr",
            "raw",
            "output",
            "search_block",
            "replace_block",
            "code",
        }

        if depth > max_depth:
            return "<omitted: depth limit>"

        if isinstance(value, str):
            return self._truncate_text(value, max_str)

        if isinstance(value, list):
            items = [self._compact_data_for_context(v, depth + 1) for v in value[:max_list]]
            if len(value) > max_list:
                items.append(f"...(+{len(value) - max_list} more)")
            return items

        if isinstance(value, dict):
            compact: Dict[str, Any] = {}
            for i, (key, val) in enumerate(value.items()):
                if i >= max_dict_keys:
                    compact["_omitted_keys"] = len(value) - max_dict_keys
                    break

                if isinstance(val, str) and key in heavy_string_keys:
                    compact[key] = self._truncate_text(val, max_str)
                    if len(val) > max_str:
                        compact[f"{key}_chars"] = len(val)
                else:
                    compact[key] = self._compact_data_for_context(val, depth + 1)
            return compact

        return value

    def _sanitize_tool_arguments_for_context(self, tool_name: str, args_str: str) -> str:
        """Condense historical tool-call arguments (especially large write/edit payloads)."""
        max_str = max(120, self.config.context_projection_max_string_chars)
        try:
            data = json.loads(args_str or "{}")
        except Exception:
            return self._truncate_text(args_str or "", max_str)

        if not isinstance(data, dict):
            return json.dumps(self._compact_data_for_context(data), ensure_ascii=False)

        compact: Dict[str, Any] = {}
        for key, val in data.items():
            if key in {"content", "search_block", "replace_block", "code"} and isinstance(val, str):
                compact[key] = f"<omitted {len(val)} chars>"
                compact[f"{key}_preview"] = self._truncate_text(val, min(220, max_str))
            else:
                compact[key] = self._compact_data_for_context(val)

        compact["_projection"] = f"args_condensed:{tool_name}"
        return json.dumps(compact, ensure_ascii=False)

    def _compact_tool_result_for_context(self, content: str, tool_name: Optional[str]) -> str:
        """Condense historical tool outputs while preserving key metadata."""
        max_str = max(120, self.config.context_projection_max_string_chars)

        try:
            parsed = json.loads(content)
            compact = self._compact_data_for_context(parsed)
            if isinstance(compact, dict):
                compact["_projection"] = "result_condensed"
                if tool_name:
                    compact["_tool"] = tool_name
            return json.dumps(compact, ensure_ascii=False)
        except Exception:
            return self._truncate_text(content, max_str)

    def _project_message_for_context(
        self,
        msg: Dict[str, Any],
        tool_name_by_call_id: Dict[str, str],
    ) -> Dict[str, Any]:
        """Project an old message into a compact form suitable for model context."""
        role = msg.get("role")

        if role == "user":
            max_user = max(300, self.config.context_projection_user_max_chars)
            return {
                "role": "user",
                "content": self._truncate_text(msg.get("content", "") or "", max_user),
            }

        if role == "assistant":
            max_assistant = max(400, self.config.context_projection_max_string_chars * 2)
            projected: Dict[str, Any] = {
                "role": "assistant",
                "content": self._truncate_text(msg.get("content", "") or "", max_assistant),
            }
            if "tool_calls" in msg:
                projected_calls = []
                for tc in msg.get("tool_calls", []):
                    fn = tc.get("function", {}) or {}
                    tc_id = tc.get("id")
                    tc_name = fn.get("name", "")
                    if tc_id and tc_name:
                        tool_name_by_call_id[tc_id] = tc_name
                    projected_calls.append(
                        {
                            "id": tc_id,
                            "type": "function",
                            "function": {
                                "name": tc_name,
                                "arguments": self._sanitize_tool_arguments_for_context(
                                    tc_name,
                                    fn.get("arguments", "") or "",
                                ),
                            },
                        }
                    )
                projected["tool_calls"] = projected_calls
            return projected

        if role == "tool":
            tool_call_id = msg.get("tool_call_id")
            tool_name = tool_name_by_call_id.get(tool_call_id or "")
            return {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": self._compact_tool_result_for_context(
                    msg.get("content", "") or "",
                    tool_name,
                ),
            }

        # System and any unknown role are passed through untouched.
        return msg

    def _summarize_messages_for_projection(self, messages: List[Dict[str, Any]]) -> str:
        """Create a compact timeline summary of older conversation context."""
        if not messages:
            return ""

        max_summary_chars = max(800, self.config.context_projection_summary_max_chars)
        max_line_chars = max(120, self.config.context_projection_max_string_chars)
        tool_name_by_call_id: Dict[str, str] = {}

        lines = [
            "AUTO-COMPACTED HISTORY (older context condensed):",
            "Use this as reference for prior decisions and tool outcomes.",
        ]

        for msg in messages:
            role = msg.get("role")
            if role == "user":
                text = self._truncate_text(msg.get("content", "") or "", max_line_chars)
                lines.append(f"- User: {text}")
            elif role == "assistant":
                text = msg.get("content", "") or ""
                if text:
                    lines.append(f"- Assistant: {self._truncate_text(text, max_line_chars)}")
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls[:4]:
                    fn = tc.get("function", {}) or {}
                    tc_id = tc.get("id")
                    tc_name = fn.get("name", "")
                    if tc_id and tc_name:
                        tool_name_by_call_id[tc_id] = tc_name
                    compact_args = self._sanitize_tool_arguments_for_context(
                        tc_name,
                        fn.get("arguments", "") or "",
                    )
                    lines.append(
                        f"- ToolCall {tc_name}: {self._truncate_text(compact_args, max_line_chars)}"
                    )
                if len(tool_calls) > 4:
                    lines.append(f"- ToolCall: ...(+{len(tool_calls) - 4} more)")
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id")
                tool_name = tool_name_by_call_id.get(tool_call_id or "", "tool")
                compact_result = self._compact_tool_result_for_context(
                    msg.get("content", "") or "",
                    tool_name,
                )
                lines.append(
                    f"- ToolResult {tool_name}: {self._truncate_text(compact_result, max_line_chars)}"
                )

            # Early exit if we already exceeded the target summary size
            if sum(len(line) + 1 for line in lines) > max_summary_chars:
                lines.append("- ...[older events truncated in summary]...")
                break

        return self._truncate_text("\n".join(lines), max_summary_chars)

    def _build_model_messages(self) -> List[Dict[str, Any]]:
        """Build projected messages for the model while keeping raw history for logging."""
        context_messages = self._context_pruning.build_model_messages(self.messages)
        self._last_pruning_stats = dict(self._context_pruning.last_stats)

        if not self.config.enable_context_projection:
            self._last_projection_stats = {
                "enabled": False,
                "active": False,
                "original_chars": self._estimate_message_payload_chars(context_messages),
                "projected_chars": self._estimate_message_payload_chars(context_messages),
                "original_tokens_est": self._estimate_message_payload_tokens(context_messages),
                "projected_tokens_est": self._estimate_message_payload_tokens(context_messages),
                "messages_projected": 0,
            }
            return context_messages

        original_chars = self._estimate_message_payload_chars(context_messages)
        original_tokens = self._estimate_message_payload_tokens(context_messages)
        token_trigger = max(0, self.config.context_projection_trigger_tokens)
        char_trigger = max(0, self.config.context_projection_trigger_chars)
        should_project = False
        if token_trigger > 0 and original_tokens >= token_trigger:
            should_project = True
        elif char_trigger > 0 and original_chars >= char_trigger:
            should_project = True

        if not should_project:
            self._last_projection_stats = {
                "enabled": True,
                "active": False,
                "original_chars": original_chars,
                "projected_chars": original_chars,
                "original_tokens_est": original_tokens,
                "projected_tokens_est": original_tokens,
                "messages_projected": 0,
            }
            return context_messages

        keep_recent = max(0, self.config.context_projection_keep_recent_messages)
        cutoff = max(1, len(context_messages) - keep_recent)
        tool_name_by_call_id: Dict[str, str] = {}
        projected: List[Dict[str, Any]] = []
        projected_count = 0
        recent_compact_window = 2

        system_message = context_messages[0]
        older_messages = context_messages[1:cutoff]
        recent_messages = context_messages[cutoff:]

        # Pre-register tool names for consistent tool-result labeling.
        for msg in context_messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []):
                    fn = tc.get("function", {}) or {}
                    tc_id = tc.get("id")
                    tc_name = fn.get("name", "")
                    if tc_id and tc_name:
                        tool_name_by_call_id[tc_id] = tc_name

        projected.append(system_message)

        summary_text = self._summarize_messages_for_projection(older_messages)
        if summary_text:
            projected.append({"role": "assistant", "content": summary_text})
            projected_count += len(older_messages)

        # Keep only a tiny raw tail; compact the rest of the recent window.
        for idx, msg in enumerate(recent_messages):
            if idx < max(0, len(recent_messages) - recent_compact_window):
                projected.append(self._project_message_for_context(msg, tool_name_by_call_id))
                projected_count += 1
            else:
                projected.append(msg)

        projected_chars = self._estimate_message_payload_chars(projected)
        projected_tokens = self._estimate_message_payload_tokens(projected)
        self._last_projection_stats = {
            "enabled": True,
            "active": True,
            "original_chars": original_chars,
            "projected_chars": projected_chars,
            "original_tokens_est": original_tokens,
            "projected_tokens_est": projected_tokens,
            "messages_projected": projected_count,
            "keep_recent_messages": keep_recent,
            "summary_chars": len(summary_text),
        }
        return projected

    def _call_model_streaming(self) -> tuple[str, List[Any], Dict[str, int]]:
        """Call LLM with streaming. All API details handled by client."""
        model_messages = self._build_model_messages()
        if self._last_projection_stats.get("active"):
            self._log("context_projection", **self._last_projection_stats)
        return self.client.chat_completion_streaming(
            messages=model_messages,
            tools=self._get_tool_specs(),
            model=self.config.model,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
            seed=self.config.seed,
            max_tokens=self.config.max_tokens,
            reasoning=self.config.reasoning,
            tool_choice="auto",
            provider=self.config.provider or None,
            openrouter_extra_body=self.config.openrouter_extra_body,
            openrouter_prompt_caching=self.config.openrouter_prompt_caching,
            openrouter_prompt_cache_ttl=self.config.openrouter_prompt_cache_ttl,
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
        if self.stream_callback:
            self.stream_callback("tool_start", {"name": name, "summary": args_summary})
        else:
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
            if self.stream_callback:
                self.stream_callback("tool_result", {"name": name, "result": result_str[:2000]})
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            }
        except UserInputRequired as e:
            # Annotate with tool call metadata so the caller can resume later
            e.tool_name = name
            e.tool_call_id = tool_call.id
            raise
        except Exception as e:
            result_str = json.dumps(
                {"error": f"Tool {name} raised an exception: {e!r}", "args": args},
                ensure_ascii=False,
            )
            self._log("tool_run_exception", tool=name, args=args, error=str(e))
            if self.stream_callback:
                self.stream_callback("tool_error", {"name": name, "error": str(e)})
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            }

    # ------------- public API -------------

    def start_session(self) -> None:
        """Start/clear a session, keeping the system prompt."""
        self._context_pruning.reset()
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def step(self, user_input: str) -> str:
        """One user turn + tool loop, appending to existing history.

        Raises:
            AgentTerminationException: If the agent terminates prematurely or
                reaches max_steps without completing the task.
            UserInputRequired: If ask_user / confirm_action needs input from
                the user.  Call ``resume_after_user_input(answer)`` to continue.
        """
        if not self.messages:
            self.start_session()

        self._log("user_input", content=user_input)
        self._context_pruning.begin_user_turn()
        self.messages.append({"role": "user", "content": user_input})

        return self._continue_step_loop(start_step=1, total_tool_calls=0)

    # ------------------------------------------------------------------
    # Human-in-the-loop resume
    # ------------------------------------------------------------------

    def resume_after_user_input(self, answer: str) -> str:
        """Continue the agent loop after the UI collected a user answer.

        This is called when a previous ``step()`` or
        ``resume_after_user_input()`` raised ``UserInputRequired``.
        The caller should pass the user's textual answer.

        Raises:
            UserInputRequired: If the agent asks *another* question.
            AgentTerminationException: On premature termination / max steps.
        """
        pending = getattr(self, "_pending_user_input", None)
        if pending is None:
            raise RuntimeError("No pending user-input request to resume from")

        exc: UserInputRequired = pending["exception"]
        tool_call = pending["tool_call"]
        remaining_tcs = pending["remaining_tool_calls"]
        state = pending["step_state"]

        self._pending_user_input = None

        # Build the tool result the model expects
        if exc.tool_name == "confirm_action":
            approved = answer.lower() in ("y", "yes", "approve")
            result = json.dumps({"approved": approved, "answer": answer})
        else:
            # ask_user
            result = json.dumps({"text": answer})

        if self.stream_callback:
            self.stream_callback(
                "tool_result", {"name": exc.tool_name, "result": result}
            )

        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
        self._context_pruning.record_tool_result(
            call_id=tool_call.id,
            tool_name=exc.tool_name,
            arguments=self._safe_load_tool_arguments(tool_call.function.arguments or "{}"),
            assistant_message_index=len(self.messages) - 2,
            tool_message_index=len(self.messages) - 1,
            result_content=result,
        )

        total_tool_calls = state["total_tool_calls"] + 1

        # Execute any remaining tool calls from the interrupted batch
        for tc in remaining_tcs:
            tool_message = self._run_tool_call(tc)
            self.messages.append(tool_message)
            self._context_pruning.record_tool_result(
                call_id=tc.id,
                tool_name=tc.function.name,
                arguments=self._safe_load_tool_arguments(tc.function.arguments or "{}"),
                assistant_message_index=len(self.messages) - 2,
                tool_message_index=len(self.messages) - 1,
                result_content=tool_message.get("content", "") or "",
            )
            total_tool_calls += 1

        return self._continue_step_loop(
            start_step=state["step_idx"] + 1,
            total_tool_calls=total_tool_calls,
        )

    # ------------------------------------------------------------------
    # Core step loop (shared by step / resume_after_user_input)
    # ------------------------------------------------------------------

    def _continue_step_loop(
        self, start_step: int, total_tool_calls: int
    ) -> str:
        last_assistant_text = ""

        for step_idx in range(start_step, self.config.max_steps + 1):
            self._log("step_start", step=step_idx)

            assistant_text, tool_calls, _ = self._call_model_streaming()
            assistant_text = strip_message_refs(assistant_text)
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
                self._log("turn_complete", step=step_idx, outcome="no_tool_calls")

                indicators = self._check_completion_indicators(assistant_text)

                if not indicators.get("task_complete", False):
                    raise AgentTerminationException(
                        message="Agent terminated without completing the task",
                        reason="Agent stopped requesting tools before task completion",
                        step_count=step_idx,
                        max_steps=self.config.max_steps,
                        last_assistant_message=assistant_text,
                        tool_calls_made=total_tool_calls,
                        diagnostic_info=indicators,
                    )

                return assistant_text

            # Execute tool calls — may raise UserInputRequired
            for i, tc in enumerate(tool_calls):
                try:
                    tool_message = self._run_tool_call(tc)
                except UserInputRequired as e:
                    # Save loop state so we can resume later
                    self._pending_user_input = {
                        "exception": e,
                        "tool_call": tc,
                        "remaining_tool_calls": list(tool_calls[i + 1:]),
                        "step_state": {
                            "step_idx": step_idx,
                            "total_tool_calls": total_tool_calls,
                        },
                    }
                    raise
                self.messages.append(tool_message)
                self._context_pruning.record_tool_result(
                    call_id=tc.id,
                    tool_name=tc.function.name,
                    arguments=self._safe_load_tool_arguments(tc.function.arguments or "{}"),
                    assistant_message_index=len(self.messages) - 2,
                    tool_message_index=len(self.messages) - 1,
                    result_content=tool_message.get("content", "") or "",
                )
                total_tool_calls += 1

        # Max steps reached
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
