"""The daily-card streak, as the bot sees it.

The streak itself lives in `tarot.RitualDay` and is counted by
`tarot.ritual.streak_for`, the same code the website uses, so a day marked in the
bot and a day marked in the Mini App are one streak, not two.

The bot has no browser to ask "what is your date?", so it uses a fixed time zone
for "today" (settings.BOT_TIMEZONE, Europe/Minsk by default — where the audience
is). The website sends the person's own date; for someone in that zone the two
agree, and a person elsewhere is at worst a day off at the midnight edge.
"""
from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction

from apps.tarot.models import RitualDay
from apps.telegram_bot.accounts import ensure_user
from apps.tarot.ritual import streak_for


def bot_today() -> datetime.date:
    tz = ZoneInfo(getattr(settings, 'BOT_TIMEZONE', 'Europe/Minsk'))
    return datetime.datetime.now(tz).date()


def days_ru(n: int) -> str:
    """'1 день', '3 дня', '5 дней' — with the 11–14 exception."""
    if 11 <= n % 100 <= 14:
        word = 'дней'
    elif n % 10 == 1:
        word = 'день'
    elif 2 <= n % 10 <= 4:
        word = 'дня'
    else:
        word = 'дней'
    return f'{n} {word}'


def _done_days(user, today: datetime.date) -> set[datetime.date]:
    since = today - datetime.timedelta(days=366)
    return set(
        RitualDay.objects.filter(user=user, day__gte=since, day__lte=today)
        .values_list('day', flat=True)
    )


def current_streak(tg_profile) -> tuple[int, bool]:
    """(streak, done_today) without creating anything. (0, False) if unlinked."""
    if tg_profile is None or tg_profile.user_id is None:
        return 0, False
    today = bot_today()
    done = _done_days(tg_profile.user, today)
    return streak_for(done, today), today in done


def check_in(tg_profile) -> tuple[int, bool]:
    """Mark today as done. Returns (streak, newly_marked).

    Idempotent: a second tap on the same day changes nothing and says so.
    """
    user = ensure_user(tg_profile)
    today = bot_today()
    created = False
    try:
        with transaction.atomic():
            _, created = RitualDay.objects.get_or_create(user=user, day=today)
    except IntegrityError:
        pass  # a concurrent tap got there first — same outcome
    return streak_for(_done_days(user, today), today), created
