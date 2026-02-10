from typing import Any, Dict

# ==============================
# Tool base class
# ==============================


class Tool:
    """
    Base interface for tools.

    Subclasses must implement:
      - name (str)
      - description (str)
      - parameters (JSON schema dict)
      - run(**kwargs) -> Any
    """

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    def get_spec(self) -> Dict[str, Any]:
        """Return OpenAI Chat Completions 'tools' entry."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def format_execution_summary(self, **kwargs) -> str:
        """
        Format a human-readable summary of what this tool execution will do.

        Override this in subclasses for more descriptive logging.
        Default implementation shows first few key-value pairs.

        Args:
            **kwargs: The arguments being passed to run()

        Returns:
            A human-readable string describing the execution
        """
        if not kwargs:
            return "(no arguments)"

        # Generic fallback: show first few key-value pairs
        items = []
        for key, value in list(kwargs.items())[:3]:
            value_str = str(value)
            # Truncate long values
            if len(value_str) > 40:
                value_str = value_str[:37] + "..."
            items.append(f"{key}={value_str}")

        summary = ", ".join(items)
        if len(kwargs) > 3:
            summary += f", ... ({len(kwargs)} total args)"

        return summary

    def run(self, **kwargs) -> Any:
        raise NotImplementedError
