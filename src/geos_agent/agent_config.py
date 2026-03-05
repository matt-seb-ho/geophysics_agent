from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    model: str = "moonshotai/kimi-k2.5"  # OpenRouter model
    provider: Optional[str] = None  # OpenRouter provider override (e.g. "baseten", "novita")
    temperature: float = 0.2
    max_tokens: int = 50000
    max_steps: int = 100  # Increased from 20 to prevent premature termination
    reasoning: bool = True
    mode: str = "auto"  # "auto" or "interactive"

    # Context configuration
    include_primer: bool = True  # Include GEOS_PRIMER.md in agent context at startup
    enable_context_projection: bool = True  # Condense old context before model calls
    context_projection_trigger_chars: int = 8000  # Trigger projection when history is large
    context_projection_keep_recent_messages: int = 3  # Keep only a tiny raw tail
    context_projection_summary_max_chars: int = 1500  # Max chars for compacted history summary
    context_projection_user_max_chars: int = 2500  # Cap older user messages
    context_projection_max_string_chars: int = 220  # Cap long strings in compacted payloads
    context_projection_max_list_items: int = 3  # Cap list lengths in compacted payloads

    # Dynamic cheatsheet (cross-session memory)
    include_cheatsheet: bool = True   # Load cheatsheet into system prompt
    curate_cheatsheet: bool = True    # Update cheatsheet after each run
    curator_model: Optional[str] = None  # Model for curation (defaults to agent model)

    # API retry configuration
    max_retries: int = 3  # Maximum number of retry attempts for API calls
    retry_delay: float = 1.0  # Initial delay between retries in seconds
    retry_backoff: float = 2.0  # Exponential backoff multiplier
    retry_on_timeout: bool = True  # Retry on timeout errors
    retry_on_rate_limit: bool = True  # Retry on rate limit errors (429)
    retry_on_server_error: bool = True  # Retry on server errors (5xx)
