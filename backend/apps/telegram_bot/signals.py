"""Pay out a referral the first time the invited person makes an interpretation.

Hooked on the credit ledger rather than on each view: every AI path (tarot, runes,
natal, numerology, horoscope) already writes a UsageLedger row through
billing.charge_credits, so this one receiver covers them all without billing
needing to know referrals exist.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.billing.models import UsageLedger

log = logging.getLogger(__name__)


@receiver(post_save, sender=UsageLedger, dispatch_uid='referral_qualify_on_first_reading')
def qualify_referral(sender, instance: UsageLedger, created: bool, **kwargs) -> None:
    from apps.telegram_bot import referrals

    if not created or instance.kind not in referrals.AI_KINDS or instance.cost_credits < 0:
        return
    try:
        referrals.qualify(instance.user)
    except Exception:  # noqa: BLE001 — a referral problem must never break a reading
        log.exception('referral qualification failed for user %s', instance.user_id)
