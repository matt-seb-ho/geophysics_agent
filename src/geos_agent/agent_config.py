from dataclasses import dataclass


@dataclass
class AgentConfig:
    model: str = "gpt-5.1-mini"  # change to your preferred model
    temperature: float = 0.1
    max_tokens: int = 2048
    max_steps: int = 10
