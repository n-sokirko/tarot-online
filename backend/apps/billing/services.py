"""Billing service layer.

Read-side: tier_for(user), has_entitlement(user, key), credits_for(user).
Write-side: charge_credits(...), grant_subscription_credits(...), grant_pack(...),
apply_subscription_activated(...), apply_subscription_canceled(...).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.billing.models import (
    CreditWallet,
    Entitlement,
    Plan,
    Subscription,
    UsageLedger,
)


# Cost table — how many credits a generation kind costs.
CREDIT_COST = {
    UsageLedger.KIND_AI_TAROT: 1,
    UsageLedger.KIND_AI_RUNES: 1,
    UsageLedger.KIND_AI_DEEP: 5,
}


@dataclass
class TierInfo:
    tier: str  # 'free' | 'premium' | 'deep'
    has_active_subscription: bool
    entitlements: set


def tier_for(user) -> TierInfo:
    """Resolve user tier from their entitlements. Anonymous users → free."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return TierInfo(tier='free', has_active_subscription=False, entitlements=set())

    valid = {e.key for e in Entitlement.objects.filter(user=user) if e.is_valid()}
    has_sub = Subscription.objects.filter(
        user=user,
        status__in=[Subscription.STATUS_ACTIVE, Subscription.STATUS_TRIALING],
    ).exists()

    if 'sonnet_ai' in valid:
        return TierInfo(tier='premium', has_active_subscription=has_sub, entitlements=valid)
    return TierInfo(tier='free', has_active_subscription=has_sub, entitlements=valid)


def has_entitlement(user, key: str) -> bool:
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    return any(
        e.key == key and e.is_valid()
        for e in Entitlement.objects.filter(user=user, key=key)
    )


def credits_balance(user) -> int:
    if user is None or not getattr(user, 'is_authenticated', False):
        return 0
    wallet, _ = CreditWallet.objects.get_or_create(user=user)
    return wallet.balance


@transaction.atomic
def charge_credits(
    *,
    user,
    kind: str,
    model_used: str = '',
    input_tokens: int = 0,
    output_tokens: int = 0,
    reference_id: str = '',
) -> tuple[bool, int]:
    """Deduct credits for an AI generation. Returns (charged, remaining_balance).

    Free-tier users with no wallet and no credits get (True, 0) — the caller
    decides whether free-tier daily limits already gate this. This function
    only enforces the credit accounting itself.
    """
    cost = CREDIT_COST.get(kind, 1)
    if user is None or not getattr(user, 'is_authenticated', False):
        UsageLedger.objects.create(
            user_id=None if user is None else getattr(user, 'id', None),
            kind=kind,
            cost_credits=0,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reference_id=reference_id,
        ) if False else None  # anonymous: don't log here
        return True, 0

    wallet, _ = CreditWallet.objects.select_for_update().get_or_create(user=user)

    # Premium users with credits → deduct. Premium with 0 credits → still allow
    # (subscription includes 50/mo grants; the next webhook tops up).
    # Free users without credits → block.
    info = tier_for(user)
    if wallet.balance >= cost:
        wallet.balance -= cost
        wallet.save(update_fields=['balance', 'updated_at'])
        UsageLedger.objects.create(
            user=user, kind=kind, cost_credits=cost,
            model_used=model_used, input_tokens=input_tokens,
            output_tokens=output_tokens, reference_id=reference_id,
        )
        return True, wallet.balance

    # Out of credits.
    if info.tier == 'premium':
        # Premium has implicit allowance even with zero credits — but we still
        # log the usage to make over-use visible and rate-limit later.
        UsageLedger.objects.create(
            user=user, kind=kind, cost_credits=0,
            model_used=model_used, input_tokens=input_tokens,
            output_tokens=output_tokens, reference_id=reference_id,
        )
        return True, 0

    return False, wallet.balance


@transaction.atomic
def grant_credits(user, amount: int, kind: str, reference_id: str = '') -> int:
    wallet, _ = CreditWallet.objects.select_for_update().get_or_create(user=user)
    wallet.balance += amount
    wallet.save(update_fields=['balance', 'updated_at'])
    UsageLedger.objects.create(
        user=user, kind=kind, cost_credits=-amount, reference_id=reference_id,
    )
    return wallet.balance


@transaction.atomic
def apply_subscription_activated(
    *,
    user,
    plan: Plan,
    paddle_subscription_id: str,
    paddle_customer_id: str = '',
    period_start=None,
    period_end=None,
) -> Subscription:
    """Idempotent: creates or updates the Subscription and the matching Entitlements."""
    period_end = period_end or (timezone.now() + timedelta(days=30))
    sub, _ = Subscription.objects.update_or_create(
        paddle_subscription_id=paddle_subscription_id,
        defaults={
            'user': user,
            'plan': plan,
            'paddle_customer_id': paddle_customer_id,
            'status': Subscription.STATUS_ACTIVE,
            'current_period_start': period_start or timezone.now(),
            'current_period_end': period_end,
            'canceled_at': None,
        },
    )

    for key in plan.entitlement_keys or []:
        Entitlement.objects.update_or_create(
            user=user, key=key,
            defaults={'expires_at': period_end, 'source': f'subscription:{plan.slug}'},
        )

    if plan.monthly_included_credits:
        grant_credits(
            user=user,
            amount=plan.monthly_included_credits,
            kind=UsageLedger.KIND_GRANT_SUB,
            reference_id=paddle_subscription_id,
        )
    return sub


@transaction.atomic
def apply_subscription_canceled(*, paddle_subscription_id: str) -> Optional[Subscription]:
    try:
        sub = Subscription.objects.select_related('user', 'plan').get(
            paddle_subscription_id=paddle_subscription_id
        )
    except Subscription.DoesNotExist:
        return None
    sub.status = Subscription.STATUS_CANCELED
    sub.canceled_at = timezone.now()
    sub.save(update_fields=['status', 'canceled_at', 'updated_at'])
    # Entitlements remain valid until expires_at — Paddle pattern is "access through period end".
    return sub


@transaction.atomic
def apply_tg_payment(*, user, plan: Plan, charge_id: str) -> None:
    """Activate a plan paid via Telegram Stars — idempotent by charge_id."""
    from datetime import timedelta

    if Subscription.objects.filter(tg_payment_charge_id=charge_id).exists():
        return

    if plan.kind == Plan.KIND_CREDITS:
        apply_pack_purchase(user=user, plan=plan, reference_id=f'tg:{charge_id}')
        return

    period_end = timezone.now() + timedelta(days=30)

    Subscription.objects.create(
        user=user,
        plan=plan,
        provider=Subscription.PROVIDER_TELEGRAM,
        tg_payment_charge_id=charge_id,
        paddle_subscription_id=None,
        status=Subscription.STATUS_ACTIVE,
        current_period_start=timezone.now(),
        current_period_end=period_end,
    )

    for key in plan.entitlement_keys or []:
        Entitlement.objects.update_or_create(
            user=user, key=key,
            defaults={'expires_at': period_end, 'source': f'telegram:{plan.slug}'},
        )

    if plan.monthly_included_credits:
        grant_credits(
            user=user,
            amount=plan.monthly_included_credits,
            kind=UsageLedger.KIND_GRANT_SUB,
            reference_id=f'tg:{charge_id}',
        )


@transaction.atomic
def apply_pack_purchase(*, user, plan: Plan, reference_id: str = '') -> int:
    if plan.kind != Plan.KIND_CREDITS or plan.credits_granted <= 0:
        return credits_balance(user)
    return grant_credits(
        user=user,
        amount=plan.credits_granted,
        kind=UsageLedger.KIND_GRANT_PACK,
        reference_id=reference_id,
    )
