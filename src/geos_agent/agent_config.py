from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContextPruningToolSettings:
    nudge_enabled: bool = True
    nudge_frequency: int = 10
    protected_tools: list[str] = field(default_factory=list)
    context_limit: int | str = 100000
    model_limits: dict[str, int | str] = field(default_factory=dict)


@dataclass
class ContextPruningPruneToolConfig:
    permission: str = "allow"


@dataclass
class ContextPruningDistillToolConfig:
    permission: str = "allow"
    show_distillation: bool = False


@dataclass
class ContextPruningCompressToolConfig:
    permission: str = "allow"
    show_compression: bool = False


@dataclass
class ContextPruningToolsConfig:
    settings: ContextPruningToolSettings = field(default_factory=ContextPruningToolSettings)
    prune: ContextPruningPruneToolConfig = field(default_factory=ContextPruningPruneToolConfig)
    distill: ContextPruningDistillToolConfig = field(default_factory=ContextPruningDistillToolConfig)
    compress: ContextPruningCompressToolConfig = field(default_factory=ContextPruningCompressToolConfig)


@dataclass
class ContextPruningManualModeConfig:
    enabled: bool = False
    automatic_strategies: bool = True


@dataclass
class ContextPruningTurnProtectionConfig:
    enabled: bool = False
    turns: int = 4


@dataclass
class ContextPruningDeduplicationConfig:
    enabled: bool = True
    protected_tools: list[str] = field(default_factory=list)


@dataclass
class ContextPruningSupersedeWritesConfig:
    enabled: bool = True


@dataclass
class ContextPruningPurgeErrorsConfig:
    enabled: bool = True
    turns: int = 4
    protected_tools: list[str] = field(default_factory=list)


@dataclass
class ContextPruningStrategiesConfig:
    deduplication: ContextPruningDeduplicationConfig = field(default_factory=ContextPruningDeduplicationConfig)
    supersede_writes: ContextPruningSupersedeWritesConfig = field(default_factory=ContextPruningSupersedeWritesConfig)
    purge_errors: ContextPruningPurgeErrorsConfig = field(default_factory=ContextPruningPurgeErrorsConfig)


@dataclass
class ContextPruningConfig:
    enabled: bool = True
    debug: bool = False
    protected_file_patterns: list[str] = field(default_factory=list)
    manual_mode: ContextPruningManualModeConfig = field(default_factory=ContextPruningManualModeConfig)
    turn_protection: ContextPruningTurnProtectionConfig = field(default_factory=ContextPruningTurnProtectionConfig)
    tools: ContextPruningToolsConfig = field(default_factory=ContextPruningToolsConfig)
    strategies: ContextPruningStrategiesConfig = field(default_factory=ContextPruningStrategiesConfig)


@dataclass
class AgentConfig:
    model: str = "moonshotai/kimi-k2.5"  # OpenRouter model
    provider: Optional[str] = None  # OpenRouter provider override (e.g. "baseten", "novita")
    temperature: float = 0.2
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    seed: Optional[int] = None
    max_tokens: int = 50000
    max_steps: int = 100  # Increased from 20 to prevent premature termination
    reasoning: bool = True
    openrouter_extra_body: dict = field(default_factory=dict)
    openrouter_prompt_caching: bool = True  # Enable provider prompt-caching support where available
    openrouter_prompt_cache_ttl: Optional[str] = None  # Anthropic cache TTL, e.g. "1h"
    mode: str = "auto"  # "auto" or "interactive"

    # Context configuration
    include_primer: bool = True  # Include GEOS_PRIMER.md in agent context at startup
    enable_context_projection: bool = True  # Condense old context before model calls
    context_projection_trigger_tokens: int = 200000  # Auto-compact once history reaches this estimated token count
    context_projection_trigger_chars: int = 0  # Legacy char-based fallback trigger; 0 disables it
    context_projection_keep_recent_messages: int = 3  # Keep only a tiny raw tail
    context_projection_summary_max_chars: int = 1500  # Max chars for compacted history summary
    context_projection_user_max_chars: int = 2500  # Cap older user messages
    context_projection_max_string_chars: int = 220  # Cap long strings in compacted payloads
    context_projection_max_list_items: int = 3  # Cap list lengths in compacted payloads
    context_pruning: ContextPruningConfig = field(default_factory=ContextPruningConfig)

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
