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

CHECKIN_DATA = "ritual:checkin"
DONE_DATA = "ritual:done"


def _snippet(text: str, limit: int = 240) -> str:
    """The first whole sentences of a card meaning, up to `limit` characters.

    Legacy Markdown breaks the whole message on a stray `_`, `*`, `` ` `` or `[`,
    so those are dropped rather than risking a failed send.
    """
    clean = " ".join((text or "").split())
    for ch in "_*`[]":
        clean = clean.replace(ch, "")
    if len(clean) <= limit:
        return clean
    cut = clean[:limit]
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    # Cut at a sentence end if there is one past the first few words; otherwise
    # at a word boundary.
    return cut[: end + 1] if end > 20 else cut.rsplit(" ", 1)[0] + "…"


def card_for(tg_id: int, cards: list, day: datetime.date) -> tuple:
    """The deterministic (card, is_reversed) for a person on a given day."""
    seed = hashlib.sha256(f"{day.isoformat()}|{tg_id}".encode()).digest()
    return cards[seed[0] % len(cards)], bool(seed[1] & 1)


def streak_line(streak: int, done_today: bool, *, is_ru: bool) -> str:
    from apps.telegram_bot.streak import days_ru

    if is_ru:
        if done_today:
            return f"✅ День отмечен · 🔥 серия {days_ru(streak)}"
        if streak:
            return f"🔥 Серия: {days_ru(streak)}. Отметь день, чтобы не прервать"
        return "Отметь день, чтобы начать серию 🔥"
    if done_today:
        return f"✅ Day marked · 🔥 streak: {streak}"
    if streak:
        return f"🔥 Streak: {streak} day{'s' if streak != 1 else ''}. Mark today to keep it"
    return "Mark today to start a streak 🔥"


def card_message(card, *, is_ru: bool, is_reversed: bool,
                 streak: int = 0, done_today: bool = False) -> tuple[str, str, str]:
    """Return (text, open_button_label, checkin_button_label) for the card of the day."""
    line = streak_line(streak, done_today, is_ru=is_ru)
    if is_ru:
        kws = (card.keywords_ru or [])[:3]
        rev = " (перевёрнута)" if is_reversed else ""
        meaning = card.reversed_meaning_ru if is_reversed else card.upright_meaning_ru
        text = (
            f"🌙 *Карта дня*\n\n"
            f"*{card.name_ru}*{rev}\n"
            f"_{' · '.join(kws)}_\n\n"
            f"{_snippet(meaning)}\n\n"
            f"{line}"
        )
        return text, "🔮 Разобрать подробнее", "🔥 Отметить день"
    kws = (card.keywords_en or [])[:3]
    rev = " (reversed)" if is_reversed else ""
    meaning = card.reversed_meaning_en if is_reversed else card.upright_meaning_en
    text = (
        f"🌙 *Card of the Day*\n\n"
        f"*{card.name_en}*{rev}\n"
        f"_{' · '.join(kws)}_\n\n"
        f"{_snippet(meaning)}\n\n"
        f"{line}"
    )
    return text, "🔮 Read it in depth", "🔥 Mark the day"


def card_markup(*, webapp: str, open_label: str, checkin_label: str,
                done: bool = False, is_ru: bool = True) -> dict:
    if done:
        first = {"text": "✅ День отмечен" if is_ru else "✅ Day marked", "callback_data": DONE_DATA}
    else:
        first = {"text": checkin_label, "callback_data": CHECKIN_DATA}
    return {"inline_keyboard": [
        [first],
        [{"text": open_label, "web_app": {"url": webapp}}],
    ]}


def render_card(tg_profile, cards: list, *, streak: int | None = None,
                done_today: bool | None = None) -> tuple[str, dict]:
    """The full card-of-the-day message and keyboard for one person, for today.

    Used both by the morning push and by the check-in button, which re-renders the
    same message with the streak updated. Pass `streak`/`done_today` to override
    what is stored (the button already knows the fresh values).
    """
    from apps.telegram_bot.streak import bot_today, current_streak

    card, is_reversed = card_for(tg_profile.tg_id, cards, bot_today())
    is_ru = (getattr(tg_profile, "locale", "ru") or "ru").startswith("ru")
    if streak is None or done_today is None:
        streak, done_today = current_streak(tg_profile)
    text, open_btn, checkin_btn = card_message(
        card, is_ru=is_ru, is_reversed=is_reversed, streak=streak, done_today=done_today,
    )
    markup = card_markup(webapp=_webapp(), open_label=open_btn, checkin_label=checkin_btn,
                         done=done_today, is_ru=is_ru)
    return text, markup


def send_card_push(users) -> dict:
    """Send the deterministic card-of-the-day to each user. Returns counts."""
    from apps.tarot.models import Card

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {"sent": 0, "failed": 0, "error": "TELEGRAM_BOT_TOKEN not set"}
    cards = list(Card.objects.all())
    if not cards:
        return {"sent": 0, "failed": 0, "error": "No cards seeded"}

    sent = failed = 0
    for u in users:
        text, markup = render_card(u, cards)
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
