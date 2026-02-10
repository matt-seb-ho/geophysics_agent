# geos_agent/tools/user_io.py
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from geos_agent.tools.base import Tool


@dataclass
class AskUser(Tool):
    name: str = "ask_user"
    description: str = "Ask the human a clarifying question and return their response."

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
