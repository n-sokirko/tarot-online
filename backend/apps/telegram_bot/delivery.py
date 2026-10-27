"""Sending to individual people, and remembering who we can no longer reach.

Telegram refuses a bot's message for a few permanent reasons — the person blocked
the bot, never started it (a bot cannot open a conversation), or deleted their
account. Those are worth recording: otherwise a broadcast just reports "20 failed"
and nobody knows who, or whether the count is one block or twenty.
"""
from __future__ import annotations

import requests

# Fragments of Telegram's `description` that mean "this person is unreachable".
PERMANENT = (
    'bot was blocked by the user',
    "bot can't initiate conversation",
    'chat not found',
    'user is deactivated',
    'bot was kicked',
)

_FRIENDLY = (
    ('bot was blocked by the user', 'заблокировал бота'),
    ("bot can't initiate conversation", 'не запускал бота (/start)'),
    ('chat not found', 'чат не найден (не запускал бота)'),
    ('user is deactivated', 'аккаунт удалён'),
    ('bot was kicked', 'бота удалили из чата'),
)


def explain(description: str) -> str:
    """Short Russian reason for an error description from Telegram."""
    low = (description or '').lower()
    for fragment, text in _FRIENDLY:
        if fragment in low:
            return text
    return (description or 'неизвестная ошибка')[:120]


def is_permanent(description: str) -> bool:
    low = (description or '').lower()
    return any(fragment in low for fragment in PERMANENT)


def _call(token: str, method: str, payload: dict) -> tuple[bool, str]:
    """(ok, error description). Never raises."""
    try:
        r = requests.post(f'https://api.telegram.org/bot{token}/{method}',
                          json=payload, timeout=15)
        data = r.json()
    except Exception as exc:  # noqa: BLE001 — network trouble is a failure, not a crash
        return False, f'сеть: {type(exc).__name__}'
    if r.ok and data.get('ok'):
        return True, ''
    return False, str(data.get('description') or f'HTTP {r.status_code}')


def send_text(token: str, chat_id: int, text: str, parse_mode: str = 'Markdown') -> tuple[bool, str]:
    return _call(token, 'sendMessage', {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode})


def probe(token: str, chat_id: int) -> tuple[bool, str]:
    """Can we message this person? Uses the 'typing' action, which leaves no
    message behind."""
    return _call(token, 'sendChatAction', {'chat_id': chat_id, 'action': 'typing'})


def record(profile, ok: bool, error: str = '') -> None:
    """Remember the outcome on the person, saving only when something changed."""
    blocked = (not ok) and is_permanent(error)
    reason = '' if ok else explain(error)[:200]
    if blocked == profile.bot_blocked and reason == profile.last_send_error:
        return
    profile.bot_blocked = blocked
    profile.last_send_error = reason
    profile.save(update_fields=['bot_blocked', 'last_send_error'])
