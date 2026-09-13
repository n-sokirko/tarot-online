"""Shared Telegram push senders.

Used by BOTH the daily management commands (Celery beat) and the Django admin
actions, so on-demand sends from the admin format and deliver exactly like the
scheduled ones. Each sender takes an explicit iterable of TelegramUser rows, so
the caller decides the audience (everyone, subscribers, or a single user).
"""
import datetime
import hashlib

from django.conf import settings

from apps.telegram_bot.birth import natal_birth_date


def _webapp() -> str:
    return getattr(settings, "WEBAPP_URL", "https://sokirdon.com")


def _send(token: str, chat_id: int, text: str, reply_markup: dict) -> bool:
    import requests
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": reply_markup,
            },
            timeout=15,
        )
        return bool(r.ok and r.json().get("ok"))
    except Exception:  # noqa: BLE001 — best-effort; caller counts the failure
        return False


# ── Card of the day ──────────────────────────────────────────────────────────

def card_message(card, *, is_ru: bool, is_reversed: bool) -> tuple[str, str]:
    """Return (text, button_label) for a user's card of the day."""
    if is_ru:
        kws = (card.keywords_ru or [])[:3]
        rev = " (перевёрнута)" if is_reversed else ""
        text = (
            f"🌙 *Карта дня*\n\n"
            f"*{card.name_ru}*{rev}\n"
            f"_{' · '.join(kws)}_\n\n"
            f"Что она значит именно для тебя сегодня?\n"
            f"Сделай расклад 👇"
        )
        return text, "🔮 Открыть расклад"
    kws = (card.keywords_en or [])[:3]
    rev = " (reversed)" if is_reversed else ""
    text = (
        f"🌙 *Card of the Day*\n\n"
        f"*{card.name_en}*{rev}\n"
        f"_{' · '.join(kws)}_\n\n"
        f"What does it mean for you today?\n"
        f"Draw your spread 👇"
    )
    return text, "🔮 Open a reading"


def send_card_push(users) -> dict:
    """Send the deterministic card-of-the-day to each user. Returns counts."""
    from apps.tarot.models import Card

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {"sent": 0, "failed": 0, "error": "TELEGRAM_BOT_TOKEN not set"}
    cards = list(Card.objects.all())
    if not cards:
        return {"sent": 0, "failed": 0, "error": "No cards seeded"}

    webapp = _webapp()
    today = datetime.date.today().isoformat()
    sent = failed = 0
    for u in users:
        seed = hashlib.sha256(f"{today}|{u.tg_id}".encode()).digest()
        card = cards[seed[0] % len(cards)]
        is_reversed = bool(seed[1] & 1)
        is_ru = (getattr(u, "locale", "ru") or "ru").startswith("ru")
        text, btn = card_message(card, is_ru=is_ru, is_reversed=is_reversed)
        markup = {"inline_keyboard": [[{"text": btn, "web_app": {"url": webapp}}]]}
        if _send(token, u.tg_id, text, markup):
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed}


# ── Personal daily horoscope ─────────────────────────────────────────────────

def horoscope_message(horo: dict, *, is_ru: bool) -> tuple[str, str]:
    """Return (text, button_label) for a personal daily horoscope."""
    if is_ru:
        text = (
            f"🔮 *Твой гороскоп на сегодня*\n\n"
            f"*{horo['name_ru']} {horo['symbol']}* · настрой дня: _{horo['mood']}_\n\n"
            f"{horo['overall']}\n\n"
            f"🍀 Число дня: {horo['lucky_number']}   🎨 Цвет: {horo['lucky_color']}\n\n"
            f"Любовь, дела, самочувствие — полный разбор внутри 👇"
        )
        return text, "🔮 Открыть гороскоп"
    text = (
        f"🔮 *Your horoscope for today*\n\n"
        f"*{horo['name_en']} {horo['symbol']}* · mood: _{horo['mood']}_\n\n"
        f"{horo['overall']}\n\n"
        f"🍀 Lucky number: {horo['lucky_number']}   🎨 Colour: {horo['lucky_color']}\n\n"
        f"Love, work, wellbeing — the full reading inside 👇"
    )
    return text, "🔮 Open horoscope"


def send_horoscope_push(users) -> dict:
    """Send the personal horoscope to each user with a resolvable birth date.
    Users without a birth date (stored or via natal chart) are skipped. Returns counts."""
    from apps.horoscope.services import sign_for_date, daily_horoscope

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {"sent": 0, "skipped": 0, "failed": 0, "error": "TELEGRAM_BOT_TOKEN not set"}

    webapp = _webapp()
    today = datetime.date.today()
    sent = skipped = failed = 0
    for u in users:
        bd = u.birth_date or natal_birth_date(u)
        if not bd:
            skipped += 1
            continue
        if not u.birth_date:  # backfill from natal chart
            u.birth_date = bd
            u.save(update_fields=["birth_date"])
        sign = sign_for_date(bd.month, bd.day)
        if not sign:
            skipped += 1
            continue
        is_ru = (getattr(u, "locale", "ru") or "ru").startswith("ru")
        horo = daily_horoscope(sign["slug"], today, "ru" if is_ru else "en")
        text, btn = horoscope_message(horo, is_ru=is_ru)
        markup = {"inline_keyboard": [[{"text": btn, "web_app": {"url": f"{webapp}/horoscope"}}]]}
        if _send(token, u.tg_id, text, markup):
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "skipped": skipped, "failed": failed}
