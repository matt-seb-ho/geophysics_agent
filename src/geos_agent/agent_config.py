from dataclasses import dataclass


@dataclass
class AgentConfig:
    model: str = "moonshotai/kimi-k2.5"  # OpenRouter model
    temperature: float = 0.1
    max_tokens: int = 50000
    max_steps: int = 20
    reasoning: bool = True
