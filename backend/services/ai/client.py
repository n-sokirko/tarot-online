"""Anthropic wrapper. Owned jointly by backend-agent and tarot-ai-agent.

backend-agent: keeps the wiring clean, handles retries, timeouts, errors,
prompt-caching headers, and model selection by tier.
tarot-ai-agent: owns the prompts (in apps/tarot/prompts/) and their parameters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

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
    """tier ∈ {'free', 'premium', 'deep'} → concrete model id.

    Premium/deep always use the Claude API. The free/budget tier uses a local
    Ollama model when LOCAL_LLM_ENABLED (marker ``local:<model>``), else Haiku.
    """
    if tier == 'premium':
        return settings.ANTHROPIC_MODEL_PREMIUM
    if tier == 'deep':
        return settings.ANTHROPIC_MODEL_DEEP
    if getattr(settings, 'LOCAL_LLM_ENABLED', False):
        return f"local:{getattr(settings, 'LOCAL_LLM_MODEL', 'qwen2.5:3b')}"
    return settings.ANTHROPIC_MODEL_FREE


# Small local models follow a short, directive prompt far better than the long,
# poetic Claude system prompt. These are tuned to reveal each card's meaning.
_LOCAL_SYS_RU = (
    "Ты — тёплый, мудрый таролог. Тебе дают вопрос человека и вытянутые карты с их позициями. "
    "Твоя задача — раскрыть значение карт и собрать их в живой поддерживающий ответ.\n\n"
    "Как отвечать:\n"
    "- Разбери каждую карту по очереди: назови её (выдели **жирным**) и объясни, что она значит "
    "именно в этой позиции и для этого вопроса. Учитывай, перевёрнута ли карта.\n"
    "- Свяжи карты в одну историю, а не в отдельные абзацы.\n"
    "- В конце дай короткий вывод и один мягкий совет.\n"
    "- Тон тёплый и образный, по-русски. Без шарлатанства и без категоричных предсказаний "
    "болезней, смертей, разводов.\n"
    "- Объём 200–350 слов. Markdown, без заголовков верхнего уровня, без эмодзи."
)
_LOCAL_SYS_EN = (
    "You are a warm, wise tarot reader. You are given the person's question and the drawn cards "
    "with their positions. Your task is to reveal the meaning of the cards and weave them into a "
    "living, supportive reading.\n\n"
    "How to answer:\n"
    "- Go through each card in turn: name it (in **bold**) and explain what it means in this "
    "position and for this question. Account for whether it is reversed.\n"
    "- Tie the cards into one story, not separate paragraphs.\n"
    "- End with a short conclusion and one gentle piece of advice.\n"
    "- Warm, vivid tone, in English. No charlatanry, no categorical predictions of illness, "
    "death, divorce.\n"
    "- Length 200–350 words. Markdown, no top-level headers, no emoji."
)


def _looks_russian(text: str) -> bool:
    return any('Ѐ' <= ch <= 'ӿ' for ch in text[:300])


def _ollama_payload(base_system_prompt, spread_system_prompt, user_message, model, max_tokens, temperature, stream):
    system = _LOCAL_SYS_RU if _looks_russian(base_system_prompt + user_message) else _LOCAL_SYS_EN
    return {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_message},
        ],
        'stream': stream,
        'options': {
            'num_predict': min(max_tokens, 900),  # 3B is slow; 200–350 words fits
            'temperature': 0.7,                    # lower = steadier for small models
            'top_p': 0.9,
            'repeat_penalty': 1.12,                # curb the small-model repetition
        },
    }


def _generate_local(base_system_prompt, spread_system_prompt, user_message, model, max_tokens, temperature):
    import requests
    url = settings.OLLAMA_URL.rstrip('/') + '/api/chat'
    resp = requests.post(
        url,
        json=_ollama_payload(base_system_prompt, spread_system_prompt, user_message, model, max_tokens, temperature, False),
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()
    return GenerationResult(
        body=(data.get('message') or {}).get('content', ''),
        model=f'local:{model}',
        input_tokens=data.get('prompt_eval_count', 0) or 0,
        output_tokens=data.get('eval_count', 0) or 0,
    )


def _stream_local(base_system_prompt, spread_system_prompt, user_message, model, max_tokens, temperature):
    import json as _json
    import requests
    url = settings.OLLAMA_URL.rstrip('/') + '/api/chat'
    parts: list[str] = []
    with requests.post(
        url,
        json=_ollama_payload(base_system_prompt, spread_system_prompt, user_message, model, max_tokens, temperature, True),
        stream=True, timeout=300,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            obj = _json.loads(line)
            chunk = (obj.get('message') or {}).get('content', '')
            if chunk:
                parts.append(chunk)
                yield ('delta', chunk)
            if obj.get('done'):
                yield ('done', GenerationResult(
                    body=''.join(parts),
                    model=f'local:{model}',
                    input_tokens=obj.get('prompt_eval_count', 0) or 0,
                    output_tokens=obj.get('eval_count', 0) or 0,
                ))


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
    chosen_model = model or settings.ANTHROPIC_MODEL_FREE
    if chosen_model.startswith('local:'):
        return _generate_local(base_system_prompt, spread_system_prompt, user_message,
                               chosen_model[len('local:'):], max_tokens, temperature)

    client = get_client()
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


def stream_interpretation(
    *,
    base_system_prompt: str,
    spread_system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int = 1500,
    temperature: float = 0.85,
) -> Iterator[Tuple[str, object]]:
    """Generator for live (SSE) generation.

    Yields ('delta', text_chunk) for each streamed token, then exactly one
    ('done', GenerationResult) with the full body + usage at the end.
    """
    chosen_model = model or settings.ANTHROPIC_MODEL_FREE
    if chosen_model.startswith('local:'):
        yield from _stream_local(base_system_prompt, spread_system_prompt, user_message,
                                 chosen_model[len('local:'):], max_tokens, temperature)
        return

    client = get_client()
    system = [
        {'type': 'text', 'text': base_system_prompt, 'cache_control': {'type': 'ephemeral'}},
        {'type': 'text', 'text': spread_system_prompt},
    ]
    parts: list[str] = []
    with client.messages.stream(
        model=chosen_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{'role': 'user', 'content': user_message}],
    ) as stream:
        for text in stream.text_stream:
            parts.append(text)
            yield ('delta', text)
        final = stream.get_final_message()

    usage = final.usage
    yield ('done', GenerationResult(
        body=''.join(parts),
        model=final.model,
        input_tokens=getattr(usage, 'input_tokens', 0) or 0,
        output_tokens=getattr(usage, 'output_tokens', 0) or 0,
        cache_creation_input_tokens=getattr(usage, 'cache_creation_input_tokens', 0) or 0,
        cache_read_input_tokens=getattr(usage, 'cache_read_input_tokens', 0) or 0,
    ))
