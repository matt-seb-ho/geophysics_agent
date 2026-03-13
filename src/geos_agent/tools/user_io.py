# geos_agent/tools/user_io.py
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from geos_agent.tools.base import Tool


class UserInputRequired(Exception):
    """Raised by IO tools when they need user input in a non-CLI context.

    The agent catches this, saves its loop state, and re-raises so the
    calling UI (e.g. Streamlit) can display the question and later call
    ``agent.resume_after_user_input(answer)``.
    """

    def __init__(
        self,
        question: str,
        choices: Optional[List[str]] = None,
        default: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        allow_custom_input: bool = False,
    ):
        self.question = question
        self.choices = choices
        self.default = default
        self.fields = fields
        self.allow_custom_input = allow_custom_input
        # Filled in by GeosAgent._run_tool_call when it catches this
        self.tool_name: str = ""
        self.tool_call_id: str = ""
        super().__init__(question)


@dataclass
class AskUser(Tool):
    name: str = "ask_user"
    description: str = "Ask the human a clarifying question and return their response. Supports simple choices or structured form fields."
    blocking: bool = True  # False = raise UserInputRequired instead of input()

    def get_spec(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The prompt shown to the user.",
                        },
                        "choices": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional quick-pick button choices.",
                        },
                        "default": {
                            "type": "string",
                            "description": "Optional default response.",
                        },
                        "allow_custom_input": {"type": "boolean", "default": False},
                        "fields": {
                            "type": "array",
                            "description": "Optional structured form controls to render inline. Use this for dropdowns, radios, checkboxes, text inputs, or textareas.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Stable field identifier."},
                                    "label": {"type": "string", "description": "User-facing field label."},
                                    "type": {
                                        "type": "string",
                                        "enum": ["text", "textarea", "select", "radio", "checkbox"],
                                        "description": "Control type to render.",
                                    },
                                    "options": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Allowed options for select, radio, or checkbox fields.",
                                    },
                                    "default": {
                                        "oneOf": [
                                            {"type": "string"},
                                            {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                        ],
                                        "description": "Optional default value. For checkbox fields, pass an array of selected options.",
                                    },
                                    "placeholder": {"type": "string", "description": "Optional placeholder text."},
                                    "required": {"type": "boolean", "default": False},
                                },
                                "required": ["id", "label", "type"],
                            },
                        },
                        "multiline": {"type": "boolean", "default": False},
                        "end_marker": {"type": "string", "default": "EOF"},
                    },
                    "required": ["question"],
                },
            },
        }

    def format_execution_summary(self, question: str, **kwargs) -> str:
        question_preview = question[:60] + "..." if len(question) > 60 else question
        return f"asking: '{question_preview}'"

    def run(
        self,
        question: str,
        choices: Optional[List[str]] = None,
        default: Optional[str] = None,
        allow_custom_input: bool = False,
        fields: Optional[List[Dict[str, Any]]] = None,
        multiline: bool = False,
        end_marker: str = "EOF",
    ) -> Dict[str, Any]:
        if not self.blocking:
            raise UserInputRequired(
                question=question,
                choices=choices,
                default=default,
                fields=fields,
                allow_custom_input=allow_custom_input,
            )

        # --- CLI mode (original behaviour) ---
        prompt = question
        if choices:
            prompt += "\nChoices:\n" + "\n".join(f"- {c}" for c in choices)
        if fields:
            prompt += "\nForm fields:"
            for field_def in fields:
                field_type = field_def.get("type", "text")
                field_label = field_def.get("label", field_def.get("id", "field"))
                prompt += f"\n- {field_label} [{field_type}]"
                options = field_def.get("options") or []
                if options:
                    prompt += f" options={', '.join(str(option) for option in options)}"
        if default is not None:
            prompt += f"\nDefault: {default}"
        prompt += "\n> "

        print(prompt, flush=True)

        if fields:
            answers: Dict[str, Any] = {}
            print(question, flush=True)
            for field_def in fields:
                field_id = str(field_def.get("id", "")).strip()
                label = str(field_def.get("label", field_id or "Field"))
                field_type = str(field_def.get("type", "text"))
                options = [str(option) for option in (field_def.get("options") or [])]
                required = bool(field_def.get("required", False))
                field_default = field_def.get("default")
                placeholder = str(field_def.get("placeholder", "") or "")

                while True:
                    field_prompt = f"{label}"
                    if options:
                        field_prompt += f" ({', '.join(options)})"
                    if field_default not in (None, "", []):
                        if isinstance(field_default, list):
                            field_prompt += f" [default: {', '.join(str(item) for item in field_default)}]"
                        else:
                            field_prompt += f" [default: {field_default}]"
                    if placeholder:
                        field_prompt += f" [{placeholder}]"
                    if not required:
                        field_prompt += " [optional]"
                    field_prompt += "\n> "
                    print(field_prompt, end="", flush=True)

                    if field_type == "textarea":
                        print(
                            f"(Enter multi-line input. End with a line containing only {end_marker})"
                        )
                        lines: List[str] = []
                        while True:
                            line = input()
                            if line.strip() == end_marker:
                                break
                            lines.append(line)
                        value: Any = "\n".join(lines).strip()
                    else:
                        raw = input().strip()
                        if field_type == "checkbox":
                            value = [item.strip() for item in raw.split(",") if item.strip()]
                        else:
                            value = raw

                    is_empty = len(value) == 0 if isinstance(value, list) else not str(value).strip()
                    if is_empty and field_default not in (None, "", []):
                        answers[field_id] = field_default
                        break
                    if is_empty and not required:
                        answers[field_id] = value
                        break
                    if not is_empty:
                        answers[field_id] = value
                        break
                    print("A value is required for this field.", flush=True)

            return {"text": json.dumps(answers), "answers": answers}

        if multiline:
            print(
                f"(Enter multi-line input. End with a line containing only {end_marker})"
            )
            lines: List[str] = []
            while True:
                line = input()
                if line.strip() == end_marker:
                    break
                lines.append(line)
            text = "\n".join(lines).strip()
        else:
            text = input().strip()

        if not text and default is not None:
            text = default

        return {"text": text}


@dataclass
class ConfirmAction(Tool):
    name: str = "confirm_action"
    description: str = (
        "Ask the human to approve or deny a potentially destructive action."
    )
    blocking: bool = True  # False = raise UserInputRequired instead of input()

    def get_spec(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "details": {"type": "string"},
                        "default": {
                            "type": "string",
                            "enum": ["approve", "deny"],
                            "default": "deny",
                        },
                    },
                    "required": ["summary"],
                },
            },
        }

    def format_execution_summary(self, summary: str, **kwargs) -> str:
        summary_preview = summary[:60] + "..." if len(summary) > 60 else summary
        return f"confirming: '{summary_preview}'"

    def run(
        self, summary: str, details: str = "", default: str = "deny"
    ) -> Dict[str, Any]:
        if not self.blocking:
            question = summary
            if details:
                question += f"\n\nDetails:\n{details}"
            raise UserInputRequired(
                question=question,
                choices=["approve", "deny"],
                default=default,
            )

        # --- CLI mode (original behaviour) ---
        print("\n=== ACTION CONFIRMATION ===")
        print(summary)
        if details:
            print("\nDetails:\n" + details)
        print("\nApprove? (y/N): ", end="", flush=True)
        ans = input().strip().lower()
        approved = ans in ("y", "yes")
        if not ans:
            approved = default == "approve"
        return {"approved": approved, "answer": ans}
