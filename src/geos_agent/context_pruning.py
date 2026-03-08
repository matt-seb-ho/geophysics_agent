import copy
import json
import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any, Dict, Iterable, List, Optional

from geos_agent.agent_config import AgentConfig
from geos_agent.tools.base import Tool


PRUNED_TOOL_OUTPUT_REPLACEMENT = (
    "[Output removed to save context - information superseded or no longer needed]"
)
PRUNED_TOOL_ERROR_INPUT_REPLACEMENT = "[input removed due to failed tool call]"
DISTILLED_TOOL_OUTPUT_REPLACEMENT = (
    "[Output distilled to save context - see distilled context notes]"
)
REMOVED_WRITE_TOOL_REPLACEMENT = "[superseded write/edit tool call removed]"
MESSAGE_REF_TAG = "<dcp-message-id>{ref}</dcp-message-id>"
MESSAGE_REF_PATTERN = re.compile(r"(?:<dcp-message-id>[^<]+</dcp-message-id>\s*)+")

DEFAULT_PROTECTED_TOOLS = {
    "ask_user",
    "confirm_action",
    "prune",
    "distill",
    "compress",
}


def strip_message_refs(text: str) -> str:
    """Remove injected DCP boundary tags from user-visible assistant text."""
    if not isinstance(text, str) or not text:
        return text
    cleaned = MESSAGE_REF_PATTERN.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


@dataclass
class ToolCallRecord:
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    assistant_message_index: int
    tool_message_index: int
    turn: int
    status: str
    result_content: str
    token_count: int


@dataclass
class DistillationRecord:
    tool_call_id: str
    tool_name: str
    distillation: str
    turn: int


@dataclass
class CompressedBlock:
    block_id: int
    topic: str
    summary: str
    start_index: int
    end_index: int
    anchor_index: int


@dataclass
class BoundaryRef:
    ref: str
    kind: str
    raw_index: Optional[int] = None
    block_id: Optional[int] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None


class ContextPruningManager:
    """Tracks tool history and rewrites the model-visible transcript."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.reset()

    def reset(self) -> None:
        self.current_turn = 0
        self.nudge_counter = 0
        self.last_tool_prune = False
        self.tool_records: Dict[str, ToolCallRecord] = {}
        self.tool_order: List[str] = []
        self.pruned_tool_ids: set[str] = set()
        self.pruned_tool_origins: Dict[str, str] = {}
        self.distillations: Dict[str, DistillationRecord] = {}
        self.compressed_blocks: List[CompressedBlock] = []
        self.total_pruned_tokens = 0
        self.last_stats: Dict[str, Any] = {
            "enabled": bool(self.config.context_pruning.enabled),
            "active": False,
            "pruned_tool_count": 0,
            "distilled_tool_count": 0,
            "compressed_block_count": 0,
            "saved_tokens_est": 0,
        }
        self._last_prunable_tool_ids: List[str] = []
        self._last_boundary_refs: List[BoundaryRef] = []
        self._last_boundary_map: Dict[str, BoundaryRef] = {}
        self._last_raw_messages: List[Dict[str, Any]] = []
        self._next_block_id = 1

    def begin_user_turn(self) -> None:
        self.current_turn += 1

    def build_tools(self) -> List[Tool]:
        if not self.config.context_pruning.enabled:
            return []

        tools: List[Tool] = []
        if self.config.context_pruning.tools.prune.permission != "deny":
            tools.append(PruneContextTool(self))
        if self.config.context_pruning.tools.distill.permission != "deny":
            tools.append(DistillContextTool(self))
        if self.config.context_pruning.tools.compress.permission != "deny":
            tools.append(CompressContextTool(self))
        return tools

    def render_system_prompt(self) -> str:
        if not self.config.context_pruning.enabled:
            return ""

        manual = self.config.context_pruning.manual_mode.enabled
        flags = {
            "prune": self.config.context_pruning.tools.prune.permission != "deny",
            "distill": self.config.context_pruning.tools.distill.permission != "deny",
            "compress": self.config.context_pruning.tools.compress.permission != "deny",
        }

        lines = [
            "",
            "=" * 80,
            "DYNAMIC CONTEXT PRUNING",
            "=" * 80,
            "This environment supports dynamic context pruning.",
        ]
        if flags["distill"]:
            lines.append(
                "- `distill`: summarize specific tool results into durable technical notes before removing raw output."
            )
        if flags["compress"]:
            lines.append(
                "- `compress`: replace a completed contiguous conversation phase with a technical summary."
            )
        if flags["prune"]:
            lines.append(
                "- `prune`: remove obsolete, noisy, or superseded tool outputs when they are no longer useful."
            )

        lines.extend(
            [
                "Use context-management tools conservatively but proactively when tool noise accumulates.",
                "Prefer distill over prune when the information may still matter later.",
                "Use compress at natural phase boundaries, not mid-investigation.",
                "Only prune tool IDs shown in the injected `<prunable-tools>` list.",
            ]
        )

        if manual:
            lines.extend(
                [
                    "Manual mode is enabled.",
                    "Do not autonomously use `prune`, `distill`, or `compress` unless the user's latest request explicitly asks for context cleanup or summarization.",
                ]
            )

        return "\n".join(lines)

    def record_tool_result(
        self,
        call_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        assistant_message_index: int,
        tool_message_index: int,
        result_content: str,
    ) -> None:
        status = self._detect_tool_status(result_content)
        token_count = self._estimate_tokens(json.dumps(arguments, ensure_ascii=False)) + self._estimate_tokens(result_content)
        record = ToolCallRecord(
            call_id=call_id,
            tool_name=tool_name,
            arguments=copy.deepcopy(arguments),
            assistant_message_index=assistant_message_index,
            tool_message_index=tool_message_index,
            turn=self.current_turn,
            status=status,
            result_content=result_content,
            token_count=token_count,
        )
        self.tool_records[call_id] = record
        if call_id not in self.tool_order:
            self.tool_order.append(call_id)

        if tool_name in {"prune", "distill", "compress"}:
            self.last_tool_prune = True
            self.nudge_counter = 0
        else:
            self.last_tool_prune = False
            self.nudge_counter += 1

    def build_model_messages(self, raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.config.context_pruning.enabled:
            self.last_stats = {
                "enabled": False,
                "active": False,
                "pruned_tool_count": 0,
                "distilled_tool_count": 0,
                "compressed_block_count": len(self.compressed_blocks),
                "saved_tokens_est": self.total_pruned_tokens,
            }
            return raw_messages

        self._last_raw_messages = copy.deepcopy(raw_messages)
        self._apply_automatic_strategies()

        visible_messages = self._build_visible_messages(raw_messages)
        visible_messages = self._append_distillation_notes(visible_messages)
        visible_messages = self._append_context_info(visible_messages)

        self.last_stats = {
            "enabled": True,
            "active": bool(self.pruned_tool_ids or self.compressed_blocks),
            "pruned_tool_count": len(self.pruned_tool_ids),
            "distilled_tool_count": len(self.distillations),
            "compressed_block_count": len(self.compressed_blocks),
            "saved_tokens_est": self.total_pruned_tokens,
            "prunable_tools": len(self._last_prunable_tool_ids),
        }
        return visible_messages

    def execute_prune(self, ids: List[str]) -> str:
        selected = self._resolve_prunable_numeric_ids(ids)
        if not selected:
            raise ValueError("No valid IDs provided. Use numeric IDs from the current <prunable-tools> list.")

        self._mark_pruned(selected, origin="prune")
        return f"Pruned {len(selected)} tool call(s): {', '.join(ids)}"

    def execute_distill(self, targets: List[Dict[str, str]]) -> str:
        if not targets:
            raise ValueError("Missing targets. Provide at least one { id, distillation } entry.")

        resolved_ids: List[str] = []
        for target in targets:
            raw_id = str(target.get("id", "")).strip()
            distillation = str(target.get("distillation", "")).strip()
            if not raw_id or not distillation:
                raise ValueError("Each distill target must include non-empty `id` and `distillation`.")
            selected = self._resolve_prunable_numeric_ids([raw_id])
            if not selected:
                raise ValueError(f"Invalid distill target id: {raw_id}")
            tool_call_id = selected[0]
            record = self.tool_records[tool_call_id]
            self.distillations[tool_call_id] = DistillationRecord(
                tool_call_id=tool_call_id,
                tool_name=record.tool_name,
                distillation=distillation,
                turn=self.current_turn,
            )
            resolved_ids.append(tool_call_id)

        self._mark_pruned(resolved_ids, origin="distill")
        return f"Distilled {len(resolved_ids)} tool call(s) into preserved notes."

    def execute_compress(self, topic: str, content: Dict[str, str]) -> str:
        start_id = str(content.get("startId", "")).strip()
        end_id = str(content.get("endId", "")).strip()
        summary = str(content.get("summary", "")).strip()
        if not topic or not start_id or not end_id or not summary:
            raise ValueError("compress requires `topic`, `content.startId`, `content.endId`, and `content.summary`.")

        start_ref = self._last_boundary_map.get(start_id)
        end_ref = self._last_boundary_map.get(end_id)
        if start_ref is None or end_ref is None:
            raise ValueError("Invalid compression boundaries. Use visible message or block IDs from the current context.")

        start_pos = self._boundary_position(start_ref.ref)
        end_pos = self._boundary_position(end_ref.ref)
        if start_pos > end_pos:
            raise ValueError("Compression boundaries are reversed.")

        included_refs = self._last_boundary_refs[start_pos : end_pos + 1]
        included_blocks = [ref for ref in included_refs if ref.kind == "block"]
        for ref in included_blocks:
            placeholder = f"({ref.ref})"
            if placeholder not in summary:
                raise ValueError(
                    f"Compression summary must include placeholder {placeholder} to preserve the existing compressed block."
                )
            block = self._get_block(ref.block_id)
            if block:
                summary = summary.replace(placeholder, block.summary)

        start_index = self._boundary_start_index(start_ref)
        end_index = self._boundary_end_index(end_ref)
        if start_index is None or end_index is None or start_index > end_index:
            raise ValueError("Unable to resolve a compressible raw message range.")

        self.compressed_blocks = [
            block
            for block in self.compressed_blocks
            if not (block.start_index >= start_index and block.end_index <= end_index)
        ]

        compressed_tool_ids = [
            call_id
            for call_id, record in self.tool_records.items()
            if start_index <= record.assistant_message_index <= end_index
            or start_index <= record.tool_message_index <= end_index
        ]
        self._mark_pruned(compressed_tool_ids, origin="compress")

        message_token_est = 0
        for idx in range(start_index, end_index + 1):
            message_token_est += self._estimate_tokens_from_message_index(idx)

        self.total_pruned_tokens += message_token_est
        block = CompressedBlock(
            block_id=self._next_block_id,
            topic=topic,
            summary=summary,
            start_index=start_index,
            end_index=end_index,
            anchor_index=start_index,
        )
        self._next_block_id += 1
        self.compressed_blocks.append(block)
        self.compressed_blocks.sort(key=lambda item: item.anchor_index)
        self.last_tool_prune = True
        self.nudge_counter = 0
        return f"Compressed messages {start_id}..{end_id} into block b{block.block_id}."

    def _apply_automatic_strategies(self) -> None:
        if self.config.context_pruning.manual_mode.enabled and not self.config.context_pruning.manual_mode.automatic_strategies:
            return

        if self.config.context_pruning.strategies.deduplication.enabled:
            self._apply_deduplication()
        if self.config.context_pruning.strategies.supersede_writes.enabled:
            self._apply_supersede_writes()
        if self.config.context_pruning.strategies.purge_errors.enabled:
            self._apply_purge_errors()

    def _apply_deduplication(self) -> None:
        protected = DEFAULT_PROTECTED_TOOLS | set(
            self.config.context_pruning.strategies.deduplication.protected_tools
        )
        signatures: Dict[str, List[str]] = {}
        for call_id in self.tool_order:
            if call_id in self.pruned_tool_ids:
                continue
            record = self.tool_records.get(call_id)
            if record is None:
                continue
            if record.tool_name in protected:
                continue
            if self._is_file_protected(record):
                continue
            signature = f"{record.tool_name}::{self._normalize_tool_signature(record.arguments)}"
            signatures.setdefault(signature, []).append(call_id)

        for ids in signatures.values():
            if len(ids) > 1:
                self._mark_pruned(ids[:-1], origin="deduplication")

    def _apply_supersede_writes(self) -> None:
        writes: Dict[str, List[str]] = {}
        reads: Dict[str, List[str]] = {}
        for call_id in self.tool_order:
            record = self.tool_records.get(call_id)
            if record is None:
                continue
            path = self._extract_primary_path(record.tool_name, record.arguments)
            if not path or self._is_file_protected(record):
                continue
            if record.tool_name in {"write_file", "edit_file"}:
                writes.setdefault(path, []).append(call_id)
            elif record.tool_name == "read_file":
                reads.setdefault(path, []).append(call_id)

        for path, write_ids in writes.items():
            read_ids = reads.get(path, [])
            if not read_ids:
                continue
            read_positions = [self.tool_order.index(call_id) for call_id in read_ids]
            for write_id in write_ids:
                if write_id in self.pruned_tool_ids:
                    continue
                write_pos = self.tool_order.index(write_id)
                if any(pos > write_pos for pos in read_positions):
                    self._mark_pruned([write_id], origin="supersede_writes")

    def _apply_purge_errors(self) -> None:
        protected = DEFAULT_PROTECTED_TOOLS | set(
            self.config.context_pruning.strategies.purge_errors.protected_tools
        )
        turn_threshold = max(1, self.config.context_pruning.strategies.purge_errors.turns)
        for call_id in self.tool_order:
            if call_id in self.pruned_tool_ids:
                continue
            record = self.tool_records.get(call_id)
            if record is None:
                continue
            if record.tool_name in protected:
                continue
            if self._is_file_protected(record):
                continue
            if record.status != "error":
                continue
            if self.current_turn - record.turn >= turn_threshold:
                self._mark_pruned([call_id], origin="purge_errors")

    def _build_visible_messages(self, raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw_messages:
            return []

        hidden_ranges = {(block.start_index, block.end_index) for block in self.compressed_blocks}
        full_remove_ids = {
            call_id
            for call_id in self.pruned_tool_ids
            if self.tool_records.get(call_id) and self.tool_records[call_id].tool_name in {"write_file", "edit_file"}
        }

        boundary_refs: List[BoundaryRef] = []
        boundary_map: Dict[str, BoundaryRef] = {}
        model_messages: List[Dict[str, Any]] = [copy.deepcopy(raw_messages[0])]
        message_ref_counter = 0

        def next_ref() -> str:
            nonlocal message_ref_counter
            ref = f"m{message_ref_counter:04d}"
            message_ref_counter += 1
            return ref

        blocks_by_anchor: Dict[int, List[CompressedBlock]] = {}
        for block in self.compressed_blocks:
            blocks_by_anchor.setdefault(block.anchor_index, []).append(block)

        for raw_index, message in enumerate(raw_messages[1:], start=1):
            for block in blocks_by_anchor.get(raw_index, []):
                ref = f"b{block.block_id}"
                boundary = BoundaryRef(
                    ref=ref,
                    kind="block",
                    block_id=block.block_id,
                    start_index=block.start_index,
                    end_index=block.end_index,
                )
                boundary_refs.append(boundary)
                boundary_map[ref] = boundary
                model_messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"{MESSAGE_REF_TAG.format(ref=ref)}\n"
                            f"Compressed Block: {block.topic}\n{block.summary}"
                        ),
                    }
                )

            if any(start <= raw_index <= end for start, end in hidden_ranges):
                continue

            transformed = copy.deepcopy(message)
            role = transformed.get("role")
            if role == "assistant":
                tool_calls = []
                for tc in transformed.get("tool_calls", []):
                    call_id = tc.get("id")
                    record = self.tool_records.get(call_id or "")
                    if call_id in full_remove_ids:
                        continue
                    if record and record.status == "error" and call_id in self.pruned_tool_ids:
                        tc = copy.deepcopy(tc)
                        fn = tc.get("function", {})
                        fn["arguments"] = self._sanitize_error_arguments(fn.get("arguments", ""))
                        tc["function"] = fn
                    tool_calls.append(tc)
                transformed["tool_calls"] = tool_calls
                content = transformed.get("content", "") or ""
                if not content and not tool_calls:
                    continue
            elif role == "tool":
                call_id = transformed.get("tool_call_id")
                record = self.tool_records.get(call_id or "")
                if call_id in full_remove_ids:
                    continue
                if record and call_id in self.pruned_tool_ids:
                    if call_id in self.distillations:
                        transformed["content"] = DISTILLED_TOOL_OUTPUT_REPLACEMENT
                    elif record.status == "completed":
                        transformed["content"] = PRUNED_TOOL_OUTPUT_REPLACEMENT

            ref = next_ref()
            boundary = BoundaryRef(ref=ref, kind="message", raw_index=raw_index)
            boundary_refs.append(boundary)
            boundary_map[ref] = boundary

            if transformed.get("role") != "system":
                content = transformed.get("content", "") or ""
                transformed["content"] = f"{MESSAGE_REF_TAG.format(ref=ref)}\n{content}".strip()
            model_messages.append(transformed)

        self._last_boundary_refs = boundary_refs
        self._last_boundary_map = boundary_map
        return model_messages

    def _append_distillation_notes(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.distillations:
            return messages

        lines = ["<distilled-context>"]
        for distillation in self.distillations.values():
            lines.append(f"- {distillation.tool_name}: {distillation.distillation}")
        lines.append("</distilled-context>")
        return [*messages, {"role": "assistant", "content": "\n".join(lines)}]

    def _append_context_info(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.config.context_pruning.manual_mode.enabled:
            self._last_prunable_tool_ids = []
            return messages

        prunable_lines: List[str] = []
        prunable_ids: List[str] = []
        protected_tools = DEFAULT_PROTECTED_TOOLS | set(self.config.context_pruning.tools.settings.protected_tools)

        for call_id in self.tool_order:
            if call_id in self.pruned_tool_ids:
                continue
            record = self.tool_records.get(call_id)
            if record is None:
                continue
            if record.tool_name in protected_tools:
                continue
            if self._is_turn_protected(record):
                continue
            if self._is_file_protected(record):
                continue
            numeric_id = len(prunable_ids)
            prunable_ids.append(call_id)
            suffix = f" (~{record.token_count} tokens)" if record.token_count else ""
            prunable_lines.append(f"{numeric_id}: {record.tool_name}{self._describe_tool_args(record.arguments)}{suffix}")

        self._last_prunable_tool_ids = prunable_ids

        extra_sections: List[str] = []
        if prunable_lines and (
            self.config.context_pruning.tools.prune.permission != "deny"
            or self.config.context_pruning.tools.distill.permission != "deny"
        ):
            extra_sections.append(
                "<prunable-tools>\n"
                "The following tools are currently eligible for context pruning.\n"
                + "\n".join(prunable_lines)
                + "\n</prunable-tools>"
            )

        if self.config.context_pruning.tools.compress.permission != "deny":
            extra_sections.append(
                "<compress-context>\n"
                f"Compress available. Conversation currently exposes {len(self._last_boundary_refs)} message/block boundaries.\n"
                "Use visible mNNNN or bN identifiers for startId/endId.\n"
                "</compress-context>"
            )

        limit = self._resolve_context_limit()
        token_est = self._estimate_tokens_for_messages(messages)
        if limit and token_est >= limit and self.config.context_pruning.tools.compress.permission != "deny":
            extra_sections.append(
                "<context-warning>\n"
                "Context usage is above the configured smart-zone limit. Prioritize compress, distill, or prune before more exploration.\n"
                "</context-warning>"
            )
        elif (
            self.config.context_pruning.tools.settings.nudge_enabled
            and self.nudge_counter >= max(1, self.config.context_pruning.tools.settings.nudge_frequency)
        ):
            enabled = [
                name
                for name, allowed in (
                    ("distill", self.config.context_pruning.tools.distill.permission != "deny"),
                    ("compress", self.config.context_pruning.tools.compress.permission != "deny"),
                    ("prune", self.config.context_pruning.tools.prune.permission != "deny"),
                )
                if allowed
            ]
            if enabled:
                extra_sections.append(
                    "<context-nudge>\n"
                    f"Context is accumulating tool noise. Consider {'/'.join(enabled)} if older tool output is no longer needed.\n"
                    "</context-nudge>"
                )

        if self.last_tool_prune:
            extra_sections.append(
                "<context-info>\n"
                "Context management just ran. Do not call prune/distill/compress again until you have made additional task progress.\n"
                "</context-info>"
            )

        if not extra_sections:
            return messages

        return [*messages, {"role": "system", "content": "\n".join(extra_sections)}]

    def _mark_pruned(self, tool_ids: Iterable[str], origin: str) -> None:
        new_ids = [tool_id for tool_id in tool_ids if tool_id and tool_id not in self.pruned_tool_ids]
        if not new_ids:
            return

        for tool_id in new_ids:
            self.pruned_tool_ids.add(tool_id)
            self.pruned_tool_origins[tool_id] = origin
            record = self.tool_records.get(tool_id)
            if record is not None:
                self.total_pruned_tokens += record.token_count

    def _resolve_prunable_numeric_ids(self, ids: List[str]) -> List[str]:
        resolved: List[str] = []
        for raw_id in ids:
            try:
                numeric = int(raw_id)
            except (TypeError, ValueError):
                continue
            if 0 <= numeric < len(self._last_prunable_tool_ids):
                resolved.append(self._last_prunable_tool_ids[numeric])
        return resolved

    def _extract_primary_path(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        if tool_name in {"read_file", "write_file", "edit_file"}:
            path = arguments.get("path")
            return str(path) if path else None
        return None

    def _is_file_protected(self, record: ToolCallRecord) -> bool:
        path = self._extract_primary_path(record.tool_name, record.arguments)
        if not path:
            return False
        return any(fnmatch(path, pattern) for pattern in self.config.context_pruning.protected_file_patterns)

    def _is_turn_protected(self, record: ToolCallRecord) -> bool:
        turn_protection = self.config.context_pruning.turn_protection
        if not turn_protection.enabled:
            return False
        return (self.current_turn - record.turn) < max(1, turn_protection.turns)

    def _resolve_context_limit(self) -> Optional[int]:
        raw_limit: Any = self.config.context_pruning.tools.settings.context_limit
        exact_limit = self.config.context_pruning.tools.settings.model_limits.get(self.config.model)
        if exact_limit is not None:
            raw_limit = exact_limit
        if isinstance(raw_limit, int):
            return raw_limit
        if isinstance(raw_limit, str) and raw_limit.endswith("%"):
            try:
                percent = max(0, min(100, int(raw_limit[:-1])))
            except ValueError:
                return None
            max_tokens = max(0, int(self.config.max_tokens))
            return (percent * max_tokens) // 100 if max_tokens else None
        return None

    def _normalize_tool_signature(self, value: Any) -> str:
        if isinstance(value, dict):
            normalized = {key: self._normalize_tool_signature(val) for key, val in sorted(value.items()) if val is not None}
            return json.dumps(normalized, ensure_ascii=False, sort_keys=True)
        if isinstance(value, list):
            return json.dumps([self._normalize_tool_signature(item) for item in value], ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def _sanitize_error_arguments(self, arguments: str) -> str:
        try:
            parsed = json.loads(arguments or "{}")
        except Exception:
            return arguments
        if isinstance(parsed, dict):
            for key, value in list(parsed.items()):
                if isinstance(value, str):
                    parsed[key] = PRUNED_TOOL_ERROR_INPUT_REPLACEMENT
        return json.dumps(parsed, ensure_ascii=False)

    def _detect_tool_status(self, content: str) -> str:
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "error" in parsed:
                return "error"
        except Exception:
            pass
        return "completed"

    def _estimate_tokens(self, text: str) -> int:
        return max(0, (len(text) + 3) // 4)

    def _estimate_tokens_from_message_index(self, raw_index: int) -> int:
        if raw_index < 0 or raw_index >= len(self._last_raw_messages):
            return 0
        message = self._last_raw_messages[raw_index]
        if message.get("role") == "tool":
            return 0
        total = self._estimate_tokens(message.get("content", "") or "")
        if message.get("role") == "assistant":
            for tc in message.get("tool_calls", []):
                fn = tc.get("function", {}) or {}
                total += self._estimate_tokens(fn.get("arguments", "") or "")
        return total

    def _estimate_tokens_for_messages(self, messages: List[Dict[str, Any]]) -> int:
        total = 0
        for message in messages:
            total += self._estimate_tokens(message.get("content", "") or "")
            for tc in message.get("tool_calls", []):
                fn = tc.get("function", {}) or {}
                total += self._estimate_tokens(fn.get("arguments", "") or "")
        return total

    def _describe_tool_args(self, arguments: Dict[str, Any]) -> str:
        path = arguments.get("path")
        if isinstance(path, str) and path:
            return f" ({path})"
        command = arguments.get("command")
        if isinstance(command, str) and command:
            preview = command[:40] + "..." if len(command) > 40 else command
            return f" ({preview})"
        query = arguments.get("query")
        if isinstance(query, str) and query:
            preview = query[:40] + "..." if len(query) > 40 else query
            return f" ({preview})"
        return ""

    def _boundary_position(self, ref: str) -> int:
        for idx, item in enumerate(self._last_boundary_refs):
            if item.ref == ref:
                return idx
        raise ValueError(f"Unknown boundary ref: {ref}")

    def _boundary_start_index(self, ref: BoundaryRef) -> Optional[int]:
        if ref.kind == "message":
            return ref.raw_index
        return ref.start_index

    def _boundary_end_index(self, ref: BoundaryRef) -> Optional[int]:
        if ref.kind == "message":
            return ref.raw_index
        return ref.end_index

    def _get_block(self, block_id: Optional[int]) -> Optional[CompressedBlock]:
        if block_id is None:
            return None
        for block in self.compressed_blocks:
            if block.block_id == block_id:
                return block
        return None


class PruneContextTool(Tool):
    name = "prune"
    description = (
        "Remove obsolete or noisy tool outputs from context. "
        "Use numeric IDs from the injected <prunable-tools> list."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Numeric IDs from the current <prunable-tools> list.",
            }
        },
        "required": ["ids"],
    }

    def __init__(self, manager: ContextPruningManager):
        self.manager = manager

    def format_execution_summary(self, ids: List[str], **kwargs) -> str:
        return f"pruning {len(ids)} tool outputs"

    def run(self, ids: List[str]) -> Dict[str, Any]:
        return {"status": "ok", "message": self.manager.execute_prune(ids)}


class DistillContextTool(Tool):
    name = "distill"
    description = (
        "Preserve the value of specific tool results as concise technical notes, then remove the raw output."
    )
    parameters = {
        "type": "object",
        "properties": {
            "targets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "distillation": {"type": "string"},
                    },
                    "required": ["id", "distillation"],
                },
                "description": "List of tool IDs and their distilled summaries.",
            }
        },
        "required": ["targets"],
    }

    def __init__(self, manager: ContextPruningManager):
        self.manager = manager

    def format_execution_summary(self, targets: List[Dict[str, str]], **kwargs) -> str:
        return f"distilling {len(targets)} tool outputs"

    def run(self, targets: List[Dict[str, str]]) -> Dict[str, Any]:
        return {"status": "ok", "message": self.manager.execute_distill(targets)}


class CompressContextTool(Tool):
    name = "compress"
    description = (
        "Replace a contiguous conversation phase with a detailed technical summary. "
        "Use current visible mNNNN or bN boundary IDs."
    )
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Short label for the compressed phase.",
            },
            "content": {
                "type": "object",
                "properties": {
                    "startId": {"type": "string"},
                    "endId": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["startId", "endId", "summary"],
            },
        },
        "required": ["topic", "content"],
    }

    def __init__(self, manager: ContextPruningManager):
        self.manager = manager

    def format_execution_summary(self, topic: str, content: Dict[str, str], **kwargs) -> str:
        start_id = content.get("startId", "?")
        end_id = content.get("endId", "?")
        return f"compressing {start_id}..{end_id} as '{topic}'"

    def run(self, topic: str, content: Dict[str, str]) -> Dict[str, Any]:
        return {"status": "ok", "message": self.manager.execute_compress(topic, content)}
