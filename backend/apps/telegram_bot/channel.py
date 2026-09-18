"""Generating posts for the public channel.

Replaces the hand-written rotating pool that `marketing/autopost.py` used: that
pool held ~28 posts and the state file was at n=83, so subscribers had already
seen everything three times over. Here every post is written fresh, and the
ChannelPost table is what keeps it from repeating itself:

  * the topics of recent posts go into the prompt as an explicit ban list;
  * the wording of recent posts is compared by fingerprint/Jaccard, and a post
    that is too close to a recent one is thrown away and re-generated.

The model is asked for JSON so the topic label can be stored separately from the
body — the label is what the ban list is built from, so it has to survive.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import re
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)

# How much history to show the model, and how far back to look for near-dupes.
BAN_LIST_SIZE = 60
SIMILARITY_WINDOW = 120
# Jaccard overlap of significant words above which two posts are "the same post".
# 0.5 is deliberately strict: these are short texts that share a lot of domain
# vocabulary (карта, аркан, колода), so real duplicates score far higher.
SIMILARITY_LIMIT = 0.5
MAX_ATTEMPTS = 4

# Two facts to one promo — the ratio the old rotation used and the one that kept
# the channel from reading as an ad feed.
PROMO_EVERY = 3

# Angles are rotated so consecutive posts do not all end up being "here is what
# arcanum N means". The model gets one angle per run and has to stay inside it.
ANGLES = [
    'историческая деталь: происхождение, датировки, как менялась традиция',
    'этимология и язык: откуда взялось слово, что оно значило изначально',
    'искусство и колоды: художники, символика изображений, различия колод',
    'психология и архетипы: как это читают Юнг и современная психология',
    'разбор одного конкретного аркана Таро, неочевидная сторона его значения',
    'разбор одной конкретной руны Старшего Футарка',
    'астрология: связь знаков, планет и домов с картами',
    'нумерология: числа в арканах и в дате рождения',
    'развенчание расхожего мифа о Таро или рунах',
    'практика: как формулировать вопрос, как читать расклад, частые ошибки',
    'культура: Таро в кино, литературе, музыке',
    'сравнение традиций: Таро, руны, И-Цзин, оракулы — чем отличаются',
]

_SYSTEM = """Ты пишешь короткие посты для Telegram-канала про Таро, руны и астрологию.

Голос канала:
— Умный, тёплый, разговорный. Как будто рассказывает увлечённый человек, а не эзотерический паблик.
— Никакого шарлатанства, пророчеств, запугивания и обещаний «узнай своё будущее».
— Никакого инфостиля: без «успей», «только сегодня», без капса и без стен из эмодзи.
— Обращение на «ты».

Жёсткие требования к фактам:
— Пиши только то, что действительно известно и проверяемо. Если не уверен в дате, имени или цифре — не пиши их вовсе, переформулируй без них.
— Не выдумывай исследования, цитаты и статистику.
— Спорные вещи подавай как спорные («считается», «по одной из версий»).

Формат:
— 3–6 коротких абзацев, всего 60–120 слов. Telegram — не лонгрид.
— Первая строка — цепляющее утверждение, выделенное тегом <b>…</b>. Можно начать с одного уместного эмодзи.
— Разметка только HTML и только теги <b>, <i>, <code>. Никакого Markdown.
— Последняя строка — мягкий, ненавязчивый переход к боту @tarott_online_bot. Каждый раз формулируй его по-новому.

Ответ отдавай строго одним JSON-объектом, без markdown-обёртки:
{"topic": "<о чём пост, 3–7 слов, по-русски>", "text": "<текст поста>"}"""

_PROMO_EXTRA = """Этот пост — промо самого бота @tarott_online_bot.

Что это за бот: онлайн-расклады Таро с живой интерпретацией от ИИ под конкретный вопрос человека, руны, натальная карта, нумерология, гороскоп и карта дня. Он не пророчит — он помогает посмотреть на свою ситуацию со стороны.

Продавай честно: через пользу и через настроение, а не через «магию» и не через давление. Не перечисляй все функции списком — возьми одну и раскрой её."""

_FACT_EXTRA = """Этот пост — интересный факт, а не реклама. Упоминание бота только в последней строке и только как мягкий переход.

Угол подачи на сегодня: {angle}

Оставайся внутри этого угла."""


@dataclass(frozen=True)
class GeneratedPost:
    kind: str
    topic: str
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    attempts: int


# Words that carry no signal for "is this the same post": stop words plus the
# domain vocabulary that shows up in literally every post.
_NOISE = {
    'это', 'этот', 'эта', 'эти', 'того', 'тому', 'там', 'так', 'такой', 'тоже',
    'что', 'чтобы', 'как', 'когда', 'где', 'если', 'или', 'ещё', 'уже', 'был',
    'была', 'были', 'быть', 'есть', 'для', 'при', 'про', 'над', 'под', 'без',
    'над', 'его', 'её', 'их', 'них', 'она', 'они', 'оно', 'все', 'весь', 'всё',
    'себя', 'свой', 'своя', 'свои', 'тебя', 'твой', 'твоя', 'тебе', 'меня',
    'один', 'одна', 'одно', 'только', 'очень', 'даже', 'просто', 'может',
    'можно', 'нужно', 'надо', 'вот', 'зато', 'потому', 'поэтому', 'чем',
    'карта', 'карты', 'карт', 'картой', 'аркан', 'арканы', 'арканов', 'колода',
    'колоды', 'таро', 'руна', 'руны', 'рун', 'бот', 'боте', 'бота',
    'tarott', 'online', 'bot',
}


def _words(text: str) -> set[str]:
    """Significant-word set used for both fingerprinting and similarity.

    Words are truncated to 5 characters as a poor man's Russian stemmer, which is
    enough to make "башня"/"башни"/"башню" collapse into one token without
    dragging in a morphology library.
    """
    plain = re.sub(r'<[^>]+>', ' ', text)
    plain = re.sub(r'[^\w\s]', ' ', plain, flags=re.UNICODE).lower()
    out = set()
    for raw in plain.split():
        if raw.isdigit() or len(raw) < 4 or raw in _NOISE:
            continue
        out.add(raw[:5])
    return out


def fingerprint(text: str) -> str:
    """Stable hash of what a post is made of. Equal fingerprints = same post."""
    return hashlib.sha256(' '.join(sorted(_words(text))).encode()).hexdigest()[:32]


def similarity(a: str, b: str) -> float:
    """Jaccard overlap of the significant words of two posts, 0.0–1.0."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def next_kind() -> str:
    """Two facts, then one promo — counted from what is actually in the table,
    so a missed or failed run cannot knock the ratio out of phase."""
    from apps.telegram_bot.models import ChannelPost

    published = ChannelPost.objects.filter(status=ChannelPost.STATUS_PUBLISHED).count()
    return ChannelPost.KIND_PROMO if published % PROMO_EVERY == PROMO_EVERY - 1 else ChannelPost.KIND_FACT


def _ban_list() -> list[str]:
    from apps.telegram_bot.models import ChannelPost

    return list(
        ChannelPost.objects.order_by('-created_at')
        .values_list('topic', flat=True)[:BAN_LIST_SIZE]
    )


def _recent_texts() -> list[str]:
    from apps.telegram_bot.models import ChannelPost

    return list(
        ChannelPost.objects.order_by('-created_at')
        .values_list('text', flat=True)[:SIMILARITY_WINDOW]
    )


def _parse(body: str) -> tuple[str, str]:
    """Pull {topic, text} out of the model's answer.

    Models wrap JSON in ```json fences often enough that stripping them is worth
    the three lines; anything else that is not parseable is a hard error, because
    silently posting a raw JSON blob to the channel would be worse.
    """
    cleaned = body.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
    data = json.loads(cleaned)
    topic = (data.get('topic') or '').strip()
    text = (data.get('text') or '').strip()
    if not topic or not text:
        raise ValueError('model returned JSON without topic/text')
    return topic[:200], text


def generate(kind: str | None = None, *, angle: str | None = None) -> GeneratedPost:
    """Write one post that does not repeat anything recent.

    Raises RuntimeError if every attempt came back as a near-duplicate — better a
    loud failure and a gap in the schedule than posting the same thing twice.
    """
    from apps.telegram_bot.models import ChannelPost
    from services.ai.client import generate_interpretation

    kind = kind or next_kind()
    bans = _ban_list()
    recent = _recent_texts()

    task = _PROMO_EXTRA if kind == ChannelPost.KIND_PROMO else _FACT_EXTRA.format(
        angle=angle or random.choice(ANGLES)
    )
    if bans:
        task += (
            '\n\nЭти темы в канале уже были — не повторяй их и не пересказывай другими словами:\n'
            + '\n'.join(f'— {t}' for t in bans)
        )

    model = settings.ANTHROPIC_MODEL_PREMIUM
    last_reason = 'no attempts made'

    for attempt in range(1, MAX_ATTEMPTS + 1):
        nudge = '' if attempt == 1 else (
            f'\n\nПредыдущая попытка вышла слишком похожей на уже опубликованное ({last_reason}). '
            'Возьми заметно другую тему.'
        )
        result = generate_interpretation(
            base_system_prompt=_SYSTEM,
            spread_system_prompt=task + nudge,
            user_message='Напиши следующий пост для канала.',
            model=model,
            max_tokens=900,
            # High: the whole point is variety, and the factual guardrails live
            # in the system prompt rather than in a low temperature.
            temperature=1.0,
        )
        try:
            topic, text = _parse(result.body)
        except (json.JSONDecodeError, ValueError) as exc:
            last_reason = f'нечитаемый ответ модели: {exc}'
            logger.warning('post_to_channel: attempt %s unparseable: %s', attempt, exc)
            continue

        worst = max((similarity(text, old) for old in recent), default=0.0)
        if worst >= SIMILARITY_LIMIT:
            last_reason = f'совпадение {worst:.0%}'
            logger.info('post_to_channel: attempt %s too similar (%.0f%%), retrying', attempt, worst * 100)
            continue

        return GeneratedPost(
            kind=kind,
            topic=topic,
            text=text,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            attempts=attempt,
        )

    raise RuntimeError(
        f'could not produce a non-repeating post in {MAX_ATTEMPTS} attempts ({last_reason})'
    )


def send_to_channel(text: str) -> int:
    """Post to the channel, returning Telegram's message id."""
    import requests

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is not set')
    chat_id = getattr(settings, 'TELEGRAM_CHANNEL_ID', '') or settings.TELEGRAM_REQUIRED_CHANNEL
    if not chat_id:
        raise RuntimeError('neither TELEGRAM_CHANNEL_ID nor TELEGRAM_REQUIRED_CHANNEL is set')

    resp = requests.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise RuntimeError(f'Telegram rejected the post: {data}')
    return data['result']['message_id']
