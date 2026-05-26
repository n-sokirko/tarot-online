"""Thin wrapper around the Anthropic SDK. Owned jointly by backend-agent and tarot-ai-agent.

backend-agent: keeps the wiring clean, handles retries, timeouts, errors.
tarot-ai-agent: owns the prompts and their parameters (model, max_tokens, temperature).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from anthropic import Anthropic


@dataclass(frozen=True)
class GenerationResult:
    body: str
    model: str
    input_tokens: int
    output_tokens: int


def get_client() -> Anthropic:
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise RuntimeError('ANTHROPIC_API_KEY not set')
    return Anthropic(api_key=key)


def generate_interpretation(
    *,
    system_prompt: str,
    user_message: str,
    model: str = 'claude-sonnet-4-6',
    max_tokens: int = 1500,
    temperature: float = 0.8,
) -> GenerationResult:
    """Synchronous one-shot. Wrap in a Celery task for production."""
    client = get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{'role': 'user', 'content': user_message}],
    )
    body = ''.join(
        block.text for block in response.content if getattr(block, 'type', None) == 'text'
    )
    return GenerationResult(
        body=body,
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
