"""Anthropic wrapper. Owned jointly by backend-agent and tarot-ai-agent.

backend-agent: keeps the wiring clean, handles retries, timeouts, errors,
prompt-caching headers, and model selection by tier.
tarot-ai-agent: owns the prompts (in apps/tarot/prompts/) and their parameters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from anthropic import Anthropic
from django.conf import settings


@dataclass(frozen=True)
class GenerationResult:
    body: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


def get_client() -> Anthropic:
    key = settings.ANTHROPIC_API_KEY
    if not key:
        raise RuntimeError('ANTHROPIC_API_KEY not set')
    # Extra resilience against transient network blips (esp. on a home uplink):
    # the SDK retries APIConnectionError / 429 / 5xx with exponential backoff.
    return Anthropic(api_key=key, max_retries=5, timeout=60.0)


def model_for_tier(tier: str) -> str:
    """tier ∈ {'free', 'premium', 'deep'} → concrete model id."""
    if tier == 'premium':
        return settings.ANTHROPIC_MODEL_PREMIUM
    if tier == 'deep':
        return settings.ANTHROPIC_MODEL_DEEP
    return settings.ANTHROPIC_MODEL_FREE


def generate_interpretation(
    *,
    base_system_prompt: str,
    spread_system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int = 1500,
    temperature: float = 0.85,
) -> GenerationResult:
    """One-shot synchronous generation with prompt caching on the base prompt.

    The base prompt (tone, ethics, format) is marked ephemeral-cached so repeated
    requests within ~5 min only pay full price the first time. The spread-specific
    prompt is sent uncached because it changes per request.
    """
    client = get_client()
    chosen_model = model or settings.ANTHROPIC_MODEL_FREE
    # Stream the response. Long generations (1500–2000 tokens) over a slow/flaky
    # uplink can drop a non-streaming connection mid-flight (APIConnectionError);
    # streaming keeps the connection warm with incremental SSE chunks and is the
    # provider-recommended path for long outputs.
    system = [
        {
            'type': 'text',
            'text': base_system_prompt,
            'cache_control': {'type': 'ephemeral'},
        },
        {
            'type': 'text',
            'text': spread_system_prompt,
        },
    ]
    with client.messages.stream(
        model=chosen_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{'role': 'user', 'content': user_message}],
    ) as stream:
        body = ''.join(stream.text_stream)
        response = stream.get_final_message()

    usage = response.usage
    return GenerationResult(
        body=body,
        model=response.model,
        input_tokens=getattr(usage, 'input_tokens', 0) or 0,
        output_tokens=getattr(usage, 'output_tokens', 0) or 0,
        cache_creation_input_tokens=getattr(usage, 'cache_creation_input_tokens', 0) or 0,
        cache_read_input_tokens=getattr(usage, 'cache_read_input_tokens', 0) or 0,
    )
