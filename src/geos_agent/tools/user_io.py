# geos_agent/tools/user_io.py
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
    ):
        self.question = question
        self.choices = choices
        self.default = default
        # Filled in by GeosAgent._run_tool_call when it catches this
        self.tool_name: str = ""
        self.tool_call_id: str = ""
        super().__init__(question)


@dataclass
class AskUser(Tool):
    name: str = "ask_user"
    description: str = "Ask the human a clarifying question and return their response."
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
                        "question": {"type": "string"},
                        "choices": {"type": "array", "items": {"type": "string"}},
                        "default": {"type": "string"},
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
        multiline: bool = False,
        end_marker: str = "EOF",
    ) -> Dict[str, Any]:
        if not self.blocking:
            raise UserInputRequired(question=question, choices=choices, default=default)

        # --- CLI mode (original behaviour) ---
        prompt = question
        if choices:
            prompt += "\nChoices:\n" + "\n".join(f"- {c}" for c in choices)
        if default is not None:
            prompt += f"\nDefault: {default}"
        prompt += "\n> "

        print(prompt, flush=True)

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
