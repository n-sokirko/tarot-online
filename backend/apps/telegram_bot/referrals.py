"""Bring a friend: invite someone, both of you get credits once they try the bot.

  1. Person A shares  t.me/<bot>?start=ref_<A's tg id>   (/invite shows it).
  2. Person B opens the link. If B was not in the bot before, a pending Referral
     is recorded — before the channel gate, so B's subscription state doesn't
     lose it.
  3. B makes their first AI interpretation. That's the qualifying moment: both
     get REWARD_CREDITS, and both are told so in the chat.

An inviter is paid for at most MAX_REWARDED friends. A referral that qualifies
after that is closed as `capped` and nobody gets anything.
"""
from __future__ import annotations

import logging
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.billing.models import UsageLedger
from apps.billing.services import CREDIT_COST, grant_credits
from apps.telegram_bot.accounts import ensure_user
from apps.telegram_bot.models import Referral, TelegramUser

log = logging.getLogger(__name__)

REWARD_CREDITS = 3
MAX_REWARDED = 5

REF_PREFIX = 'ref_'
AI_KINDS = tuple(CREDIT_COST)


def link_for(tg_id: int) -> str:
    bot = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'tarott_online_bot')
    return f'https://t.me/{bot}?start={REF_PREFIX}{tg_id}'


def share_url(tg_id: int, *, is_ru: bool) -> str:
    text = ('Гадаю в этом боте: карта дня, расклады и руны. Заходи по моей ссылке, '
            'получишь 3 бесплатных разбора.' if is_ru else
            'I use this bot for tarot spreads and runes. Join through my link '
            'and get 3 free readings.')
    return f'https://t.me/share/url?url={quote(link_for(tg_id), safe="")}&text={quote(text)}'


def parse_ref(arg: str) -> int | None:
    """tg id out of a `ref_<id>` start argument, or None."""
    if not arg.startswith(REF_PREFIX):
        return None
    raw = arg[len(REF_PREFIX):]
    return int(raw) if raw.isdigit() and len(raw) <= 15 else None


def rewarded_count(referrer: TelegramUser) -> int:
    return Referral.objects.filter(referrer=referrer, status=Referral.STATUS_REWARDED).count()


def register(invited_tg_id: int, referrer_tg_id: int, *, username: str = '',
             first_name: str = '', locale: str = 'ru') -> bool:
    """Record that `referrer` invited `invited`. True only if a new referral was made.

    Not recorded when: it is a self-invite, the inviter is unknown, the inviter is
    already at the cap, or the invited person was in the bot before (a referral is
    for people who are new).
    """
    if invited_tg_id == referrer_tg_id:
        return False
    referrer = TelegramUser.objects.filter(tg_id=referrer_tg_id).first()
    if referrer is None or rewarded_count(referrer) >= MAX_REWARDED:
        return False
    invited, created = TelegramUser.objects.get_or_create(
        tg_id=invited_tg_id,
        defaults={'tg_username': username, 'tg_first_name': first_name, 'locale': locale},
    )
    if not created:
        return False
    Referral.objects.create(referrer=referrer, invited=invited)
    return True


def stats(tg_profile: TelegramUser) -> dict:
    rewarded = rewarded_count(tg_profile)
    pending = Referral.objects.filter(
        referrer=tg_profile, status=Referral.STATUS_PENDING).count()
    return {
        'rewarded': rewarded,
        'pending': pending,
        'credits': rewarded * REWARD_CREDITS,
        'left': max(MAX_REWARDED - rewarded, 0),
    }


def qualify(user) -> Referral | None:
    """Called when `user` has just made an AI interpretation. Pays out a pending
    referral for them, once. Returns the referral if it was paid."""
    with transaction.atomic():
        ref = (
            Referral.objects.select_for_update(of=('self',))
            .select_related('referrer', 'invited')
            .filter(invited__user=user, status=Referral.STATUS_PENDING)
            .first()
        )
        if ref is None:
            return None

        # Serialise payouts per inviter so two friends qualifying at the same
        # moment cannot both slip under the cap.
        TelegramUser.objects.select_for_update().get(pk=ref.referrer_id)

        ref.qualified_at = timezone.now()
        if rewarded_count(ref.referrer) >= MAX_REWARDED:
            ref.status = Referral.STATUS_CAPPED
            ref.save(update_fields=['status', 'qualified_at'])
            return None

        inviter_user = ensure_user(ref.referrer)
        grant_credits(inviter_user, REWARD_CREDITS, UsageLedger.KIND_GRANT_REFERRAL,
                      reference_id=f'referral:{ref.pk}:inviter')
        grant_credits(user, REWARD_CREDITS, UsageLedger.KIND_GRANT_REFERRAL,
                      reference_id=f'referral:{ref.pk}:friend')
        ref.status = Referral.STATUS_REWARDED
        ref.save(update_fields=['status', 'qualified_at'])

        # Telegram calls must not run inside the DB transaction.
        transaction.on_commit(lambda: notify(ref.pk))
        return ref


def _ru(profile: TelegramUser) -> bool:
    return (profile.locale or 'ru').startswith('ru')


def notify(referral_id: int) -> None:
    """Tell both people about the reward. Best effort — never raises."""
    try:
        from apps.telegram_bot.push import _send, _webapp

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            return
        ref = Referral.objects.select_related('referrer', 'invited').get(pk=referral_id)
        done = stats(ref.referrer)
        for who, profile in (('inviter', ref.referrer), ('friend', ref.invited)):
            ru = _ru(profile)
            if who == 'inviter':
                text = (
                    f'🎁 Твой друг сделал первый разбор. Вам обоим начислено +{REWARD_CREDITS}.\n\n'
                    f'Приглашено: {done["rewarded"]} из {MAX_REWARDED}.'
                    if ru else
                    f'🎁 Your friend made their first reading. You both got +{REWARD_CREDITS}.\n\n'
                    f'Invited: {done["rewarded"]} of {MAX_REWARDED}.'
                )
            else:
                text = (
                    f'🎁 Тебе +{REWARD_CREDITS} разбора в подарок: тебя пригласил друг.'
                    if ru else
                    f'🎁 +{REWARD_CREDITS} readings for you: a friend invited you.'
                )
            button = {'text': '🔮 Открыть расклады' if ru else '🔮 Open readings',
                      'web_app': {'url': _webapp()}}
            _send(token, profile.tg_id, text, {'inline_keyboard': [[button]]})
    except Exception:  # noqa: BLE001 — the credits are already granted; a lost message is not fatal
        log.exception('referral notification failed for %s', referral_id)
