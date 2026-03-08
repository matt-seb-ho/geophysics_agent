"""
OpenRouter API client with configurable retry logic and error handling.

This module provides a wrapper around the OpenAI client that adds:
- Exponential backoff retry logic
- Configurable retry behavior for different error types
- Optional logging integration
"""

import sys
import time
from copy import deepcopy
from typing import Any, Callable, Optional, TypeVar

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

T = TypeVar("T")


class RetryConfig:
    """Configuration for API retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        retry_on_timeout: bool = True,
        retry_on_rate_limit: bool = True,
        retry_on_server_error: bool = True,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_rate_limit = retry_on_rate_limit
        self.retry_on_server_error = retry_on_server_error


class OpenRouterClient:
    """
    OpenAI-compatible client for OpenRouter with built-in retry logic.

    This wraps the OpenAI client and adds retry logic with exponential backoff
    for transient failures (timeouts, rate limits, server errors).
    """

    def __init__(
        self,
        api_key: str,
        retry_config: Optional[RetryConfig] = None,
        log_callback: Optional[Callable[[str, Any], None]] = None,
        stream_callback: Optional[Callable] = None,
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            retry_config: Retry configuration (uses defaults if None)
            log_callback: Optional callback for logging events.
                         Should accept (event_name: str, **kwargs)
            stream_callback: Optional callback for streaming events.
                         Called with (event_type: str, data: Any) where event_type
                         is one of: "text", "thinking_start", "thinking",
                         "thinking_end", "tool_start", "tool_result", "tool_error".
        """
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.retry_config = retry_config or RetryConfig()
        self.log_callback = log_callback
        self.stream_callback = stream_callback
        # Track cumulative token usage
        self.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
            "cache_write_tokens": 0,
        }

    def get_token_usage(self) -> dict:
        """Return the cumulative token usage for this client instance."""
        return self.usage

    def _log(self, event: str, **kwargs: Any) -> None:
        """Log an event if a callback is configured."""
        if self.log_callback:
            try:
                self.log_callback(event, **kwargs)
            except Exception:
                # Logging should never crash the client
                pass

    def with_retry(
        self, func: Callable[[], T], operation_name: str = "API call"
    ) -> T:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: The function to execute (should be a lambda or callable with no args)
            operation_name: Description of the operation for logging/error messages

        Returns:
            The result of the function call

        Raises:
            The last exception encountered after all retries are exhausted
        """
        last_exception = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return func()

            except APITimeoutError as e:
                last_exception = e
                if (
                    not self.retry_config.retry_on_timeout
                    or attempt >= self.retry_config.max_retries
                ):
                    print(
                        f"\n[ERROR] API timeout after {attempt + 1} attempts",
                        file=sys.stderr,
                    )
                    self._log("api_timeout", attempts=attempt + 1, error=str(e))
                    raise
                delay = self.retry_config.retry_delay * (
                    self.retry_config.retry_backoff**attempt
                )
                print(
                    f"\n[WARNING] API timeout on {operation_name} "
                    f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                    f"Retrying in {delay:.1f}s...",
                    file=sys.stderr,
                )
                self._log("api_retry", reason="timeout", attempt=attempt + 1, delay=delay)
                time.sleep(delay)

            except RateLimitError as e:
                last_exception = e
                if (
                    not self.retry_config.retry_on_rate_limit
                    or attempt >= self.retry_config.max_retries
                ):
                    print(
                        f"\n[ERROR] Rate limit exceeded after {attempt + 1} attempts",
                        file=sys.stderr,
                    )
                    self._log("api_rate_limit", attempts=attempt + 1, error=str(e))
                    raise
                # For rate limits, use longer delays
                delay = self.retry_config.retry_delay * (
                    self.retry_config.retry_backoff ** (attempt + 1)
                )
                print(
                    f"\n[WARNING] Rate limit on {operation_name} "
                    f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                    f"Retrying in {delay:.1f}s...",
                    file=sys.stderr,
                )
                self._log("api_retry", reason="rate_limit", attempt=attempt + 1, delay=delay)
                time.sleep(delay)

            except APIConnectionError as e:
                last_exception = e
                if attempt >= self.retry_config.max_retries:
                    print(
                        f"\n[ERROR] Connection error after {attempt + 1} attempts",
                        file=sys.stderr,
                    )
                    self._log("api_connection_error", attempts=attempt + 1, error=str(e))
                    raise
                delay = self.retry_config.retry_delay * (
                    self.retry_config.retry_backoff**attempt
                )
                print(
                    f"\n[WARNING] Connection error on {operation_name} "
                    f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                    f"Retrying in {delay:.1f}s...",
                    file=sys.stderr,
                )
                self._log("api_retry", reason="connection_error", attempt=attempt + 1, delay=delay)
                time.sleep(delay)

            except APIError as e:
                last_exception = e
                # Check if it's a server error (5xx)
                is_server_error = (
                    hasattr(e, "status_code")
                    and e.status_code
                    and 500 <= e.status_code < 600
                )

                if (
                    not is_server_error
                    or not self.retry_config.retry_on_server_error
                    or attempt >= self.retry_config.max_retries
                ):
                    error_type = "server error" if is_server_error else "API error"
                    print(
                        f"\n[ERROR] {error_type} after {attempt + 1} attempts: {e}",
                        file=sys.stderr,
                    )
                    self._log(
                        "api_error",
                        attempts=attempt + 1,
                        error=str(e),
                        is_server_error=is_server_error,
                    )
                    raise

                delay = self.retry_config.retry_delay * (
                    self.retry_config.retry_backoff**attempt
                )
                print(
                    f"\n[WARNING] Server error on {operation_name} "
                    f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                    f"Retrying in {delay:.1f}s...",
                    file=sys.stderr,
                )
                self._log(
                    "api_retry",
                    reason="server_error",
                    attempt=attempt + 1,
                    delay=delay,
                    status_code=getattr(e, "status_code", None),
                )
                time.sleep(delay)

            except Exception as e:
                # For unexpected errors, don't retry
                print(
                    f"\n[ERROR] Unexpected error on {operation_name}: {e}",
                    file=sys.stderr,
                )
                self._log(
                    "unexpected_error", error=str(e), error_type=type(e).__name__
                )
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic failed unexpectedly")

    @property
    def chat(self):
        """Access to the underlying chat completions API."""
        return self.client.chat

    def chat_completion_streaming(
        self,
        messages: list,
        tools: Optional[list] = None,
        model: str = "moonshotai/kimi-k2.5",
        temperature: float = 0.2,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        seed: Optional[int] = None,
        max_tokens: int = 50000,
        reasoning: bool = True,
        tool_choice: str = "auto",
        provider: Optional[str] = None,
        openrouter_extra_body: Optional[dict[str, Any]] = None,
        openrouter_prompt_caching: bool = True,
        openrouter_prompt_cache_ttl: Optional[str] = None,
    ) -> tuple[str, list, dict]:
        """
        Make a streaming chat completion call and parse the response.

        This method handles all the complexity of streaming responses including:
        - Building the request with proper parameters
        - Streaming chunks to stdout in real-time
        - Accumulating tool calls across chunks
        - Retry logic for transient failures
        - Handling reasoning/thinking content and usage statistics

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool specifications
            model: Model identifier
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            seed: Optional deterministic seed
            max_tokens: Maximum tokens to generate
            reasoning: Enable reasoning for supported models
            tool_choice: Tool choice strategy ("auto", "none", or specific tool)
            openrouter_prompt_caching: Enable provider prompt-caching support.
            openrouter_prompt_cache_ttl: Anthropic cache TTL override (e.g. "1h")

        Returns:
            Tuple of (full_text_content, tool_calls_list, usage_dict)
            where tool_calls_list contains objects with .id and .function attributes
            and usage_dict contains prompt_tokens, completion_tokens, etc.
        """

        def _make_streaming_call():
            # Build extra body for reasoning models and provider routing
            extra_body = dict(openrouter_extra_body or {})

            if reasoning:
                extra_body["reasoning"] = {"enabled": True}
            if provider:
                extra_body["provider"] = {"order": [provider]}

            request_messages, cache_control = self._prepare_messages_for_prompt_caching(
                messages=messages,
                model=model,
                provider=provider,
                enabled=openrouter_prompt_caching,
                ttl=openrouter_prompt_cache_ttl,
            )
            if cache_control:
                extra_body["cache_control"] = cache_control

            stream = self.client.chat.completions.create(
                model=model,
                messages=request_messages,
                tools=tools or [],
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                seed=seed,
                max_tokens=max_tokens,
                stream=True,
                stream_options={"include_usage": True},
                extra_body=extra_body if extra_body else None,
                tool_choice=tool_choice,
            )

            # Accumulate the response
            full_content = ""
            tool_calls_data: dict[int, dict[str, Any]] = {}  # index -> {id, name, arguments}
            usage_data = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cached_tokens": 0,
                "cache_write_tokens": 0,
            }
            
            reasoning_active = False

            try:
                for chunk in stream:
                    # Capture usage if present (usually in the last chunk)
                    if chunk.usage:
                        prompt_details = getattr(chunk.usage, "prompt_tokens_details", None)
                        cached_tokens = int(getattr(prompt_details, "cached_tokens", 0) or 0)
                        cache_write_tokens = int(
                            getattr(prompt_details, "cache_write_tokens", 0) or 0
                        )
                        # Accumulate to client instance state
                        self.usage["prompt_tokens"] += chunk.usage.prompt_tokens
                        self.usage["completion_tokens"] += chunk.usage.completion_tokens
                        self.usage["total_tokens"] += chunk.usage.total_tokens
                        self.usage["cached_tokens"] += cached_tokens
                        self.usage["cache_write_tokens"] += cache_write_tokens
                        
                        # Also track for this specific call
                        usage_data["prompt_tokens"] = chunk.usage.prompt_tokens
                        usage_data["completion_tokens"] = chunk.usage.completion_tokens
                        usage_data["total_tokens"] = chunk.usage.total_tokens
                        usage_data["cached_tokens"] = cached_tokens
                        usage_data["cache_write_tokens"] = cache_write_tokens

                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    if not delta:
                        continue

                    # Handle reasoning content
                    # Note: different providers might use different fields, trying standard approach
                    # OpenRouter/Kimi might map it to 'reasoning' or 'reasoning_content'
                    r_content = getattr(delta, "reasoning", None)
                    if r_content:
                        if not reasoning_active:
                            if self.stream_callback:
                                self.stream_callback("thinking_start", "")
                            else:
                                print("<Thinking>", end="", flush=True)
                            reasoning_active = True
                        if self.stream_callback:
                            self.stream_callback("thinking", r_content)
                        else:
                            print(r_content, end="", flush=True)

                    # Handle text content
                    if delta.content:
                        if reasoning_active:
                            if self.stream_callback:
                                self.stream_callback("thinking_end", "")
                            else:
                                print("</Thinking>\n", end="", flush=True)
                            reasoning_active = False

                        if self.stream_callback:
                            self.stream_callback("text", delta.content)
                        else:
                            print(delta.content, end="", flush=True)
                        full_content += delta.content

                    # Handle tool calls (they come in chunks)
                    if delta.tool_calls:
                        if reasoning_active:
                            if self.stream_callback:
                                self.stream_callback("thinking_end", "")
                            else:
                                print("</Thinking>\n", end="", flush=True)
                            reasoning_active = False

                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_data:
                                tool_calls_data[idx] = {
                                    "id": "",
                                    "name": "",
                                    "arguments": "",
                                }
                            if tc.id:
                                tool_calls_data[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_data[idx]["name"] = tc.function.name
                                # Handle partial arguments
                                if tc.function.arguments:
                                    tool_calls_data[idx]["arguments"] += tc.function.arguments
            except Exception as e:
                # If streaming fails mid-way, log a warning
                if full_content:
                    print(f"\n[WARNING] Streaming interrupted: {e}", file=sys.stderr)
                raise

            if reasoning_active:
                if self.stream_callback:
                    self.stream_callback("thinking_end", "")
                else:
                    print("</Thinking>\n", end="", flush=True)

            # Convert accumulated tool calls to a list of simple objects
            tool_calls = []
            for idx in sorted(tool_calls_data.keys()):
                tc_data = tool_calls_data[idx]
                # Create a simple object-like structure with .id and .function attributes
                tool_call = type(
                    "ToolCall",
                    (),
                    {
                        "id": tc_data["id"],
                        "function": type(
                            "Function",
                            (),
                            {
                                "name": tc_data["name"],
                                "arguments": tc_data["arguments"],
                            },
                        )(),
                    },
                )()
                tool_calls.append(tool_call)

            if full_content and not self.stream_callback:
                print()  # Newline after streaming

            return full_content, tool_calls, usage_data

        # Wrap in retry logic
        return self.with_retry(_make_streaming_call, "streaming chat completion")

    @staticmethod
    def _build_cache_control(ttl: Optional[str]) -> dict[str, str]:
        cache_control: dict[str, str] = {"type": "ephemeral"}
        if ttl == "1h":
            cache_control["ttl"] = "1h"
        return cache_control

    @staticmethod
    def _normalize_provider_name(provider: Optional[str]) -> Optional[str]:
        if provider is None:
            return None
        normalized = provider.strip().lower()
        return normalized or None

    @classmethod
    def _resolve_prompt_cache_strategy(
        cls,
        model: str,
        provider: Optional[str],
    ) -> str:
        """
        Decide how prompt caching should be expressed for this model/provider pair.

        Returns one of:
        - "top_level": send cache_control in extra_body
        - "explicit": add cache_control to message content blocks
        - "implicit": do not modify the request for caching
        """
        model_lower = model.lower()
        model_prefix = (model.split("/", 1)[0] if "/" in model else "").lower()
        normalized_provider = cls._normalize_provider_name(provider)

        if model_prefix == "anthropic":
            # OpenRouter's top-level automatic caching is the Anthropic-direct path.
            # If the caller pins Bedrock/Vertex (or another non-Anthropic provider),
            # fall back to explicit block-level breakpoints instead.
            if normalized_provider in {None, "anthropic"}:
                return "top_level"
            return "explicit"

        if model_prefix == "google" and "gemini" in model_lower:
            return "explicit"

        return "implicit"

    @classmethod
    def _prepare_messages_for_prompt_caching(
        cls,
        messages: list,
        model: str,
        provider: Optional[str],
        enabled: bool,
        ttl: Optional[str],
    ) -> tuple[list, Optional[dict[str, str]]]:
        if not enabled:
            return messages, None

        strategy = cls._resolve_prompt_cache_strategy(model, provider)
        cache_control = cls._build_cache_control(ttl)

        if strategy == "top_level":
            return messages, cache_control

        if strategy == "explicit":
            transformed = deepcopy(messages)
            for msg in transformed:
                if msg.get("role") not in {"system", "developer", "user"}:
                    continue
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    msg["content"] = [
                        {
                            "type": "text",
                            "text": content,
                            "cache_control": cache_control,
                        }
                    ]
                    return transformed, None
                if isinstance(content, list):
                    for block in reversed(content):
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "text"
                            and isinstance(block.get("text"), str)
                            and block.get("text", "").strip()
                        ):
                            block["cache_control"] = cache_control
                            return transformed, None
            return transformed, None

        return messages, None
