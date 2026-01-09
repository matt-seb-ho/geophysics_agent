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

    def run(self, **kwargs) -> Any:
        raise NotImplementedError
