from dataclasses import dataclass


@dataclass
class AgentConfig:
    model: str = "moonshotai/kimi-k2.5"  # OpenRouter model
    temperature: float = 0.2
    max_tokens: int = 50000
    max_steps: int = 100  # Increased from 20 to prevent premature termination
    reasoning: bool = True
    mode: str = "auto"  # "auto" or "interactive"
