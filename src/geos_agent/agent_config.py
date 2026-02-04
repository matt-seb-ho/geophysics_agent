from dataclasses import dataclass


@dataclass
class AgentConfig:
    model: str = "z-ai/glm-4.7"  # OpenRouter model
    temperature: float = 0.1
    max_tokens: int = 2048
    max_steps: int = 10
    reasoning: bool = True
