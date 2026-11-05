"""Warm-up campaign: send the promo video to the bot, get free readings once.

The TikTok/Reels warm-up video ends with "forward this video to the bot and get
3 readings for free". Anyone who sends the bot a video file gets
PROMO_VIDEO_CREDITS, once per Telegram account. The video itself is not checked
against the original — a re-encoded download from TikTok wouldn't match any hash
anyway, and the bonus is small enough that "any video, once" is the fair rule.
"""
from __future__ import annotations

from django.conf import settings
from django.db import transaction

from apps.billing.models import UsageLedger
from apps.billing.services import grant_credits
from apps.telegram_bot.accounts import ensure_user
from apps.telegram_bot.models import TelegramUser

REFERENCE = 'promo:video'


def credits() -> int:
    return int(getattr(settings, 'PROMO_VIDEO_CREDITS', 3))


def enabled() -> bool:
    return bool(getattr(settings, 'PROMO_VIDEO_ENABLED', True))


def claim_video_bonus(tg_id: int, *, username: str = '', first_name: str = '',
                      locale: str = 'ru') -> bool:
    """Grant the video bonus. True if granted now, False if this account already had it."""
    TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={'tg_username': username, 'tg_first_name': first_name, 'locale': locale},
    )
    with transaction.atomic():
        # Lock the profile so two videos sent at the same moment can't both pay out.
        profile = TelegramUser.objects.select_for_update().get(tg_id=tg_id)
        user = ensure_user(profile)
        if UsageLedger.objects.filter(user=user, kind=UsageLedger.KIND_GRANT_PROMO,
                                      reference_id=REFERENCE).exists():
            return False
        grant_credits(user, credits(), UsageLedger.KIND_GRANT_PROMO, reference_id=REFERENCE)
        return True
