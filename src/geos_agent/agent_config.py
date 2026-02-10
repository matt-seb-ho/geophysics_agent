from dataclasses import dataclass


@dataclass
class AgentConfig:
    model: str = "moonshotai/kimi-k2.5"  # OpenRouter model
    temperature: float = 0.2
    max_tokens: int = 50000
    max_steps: int = 100  # Increased from 20 to prevent premature termination
    reasoning: bool = True
    mode: str = "auto"  # "auto" or "interactive"

    # Context configuration
    include_primer: bool = True  # Include GEOS_PRIMER.md in agent context at startup

    # API retry configuration
    max_retries: int = 3  # Maximum number of retry attempts for API calls
    retry_delay: float = 1.0  # Initial delay between retries in seconds
    retry_backoff: float = 2.0  # Exponential backoff multiplier
    retry_on_timeout: bool = True  # Retry on timeout errors
    retry_on_rate_limit: bool = True  # Retry on rate limit errors (429)
    retry_on_server_error: bool = True  # Retry on server errors (5xx)
