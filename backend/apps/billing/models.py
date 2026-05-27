"""Billing models — Paddle as Merchant of Record.

Architecture:
- Plan: catalogue of products/tiers (free, premium, credit packs).
- Subscription: a user's active recurring plan, mirrored from Paddle.
- Entitlement: derived row that says "user X has access to feature Y until Z".
  Webhook handlers write here; API permissions read here.
- CreditWallet: balance of pay-as-you-go credits.
- UsageLedger: append-only log of every AI generation; used for analytics
  and for soft-limit enforcement on the premium tier.
- PaddleEvent: idempotency table — every webhook is recorded once.
"""
from django.conf import settings
from django.db import models


class Plan(models.Model):
    KIND_FREE = 'free'
    KIND_SUBSCRIPTION = 'subscription'
    KIND_CREDITS = 'credits'
    KIND_CHOICES = [
        (KIND_FREE, 'Free'),
        (KIND_SUBSCRIPTION, 'Subscription'),
        (KIND_CREDITS, 'Credit pack'),
    ]

    slug = models.SlugField(unique=True, max_length=64)
    name_ru = models.CharField(max_length=128)
    name_en = models.CharField(max_length=128)
    description_ru = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_FREE)
    price_usd_cents = models.PositiveIntegerField(default=0)

    # Paddle product/price ids (kept as strings, may be empty for free)
    paddle_product_id = models.CharField(max_length=64, blank=True)
    paddle_price_id = models.CharField(max_length=64, blank=True)

    # Telegram Stars price (0 = not available via Telegram)
    tg_stars_price = models.PositiveIntegerField(default=0)

    # For subscription plans: how many included credits per period
    monthly_included_credits = models.PositiveIntegerField(default=0)
    # For credit packs: how many credits the purchase grants
    credits_granted = models.PositiveIntegerField(default=0)

    # Which feature flags this plan unlocks (list of entitlement keys)
    entitlement_keys = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'price_usd_cents']

    def __str__(self) -> str:
        return f'{self.slug} ({self.kind})'


class Subscription(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_TRIALING = 'trialing'
    STATUS_PAST_DUE = 'past_due'
    STATUS_CANCELED = 'canceled'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_TRIALING, 'Trialing'),
        (STATUS_PAST_DUE, 'Past due'),
        (STATUS_CANCELED, 'Canceled'),
        (STATUS_PAUSED, 'Paused'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')

    PROVIDER_PADDLE = 'paddle'
    PROVIDER_TELEGRAM = 'telegram'
    PROVIDER_CHOICES = [
        (PROVIDER_PADDLE, 'Paddle'),
        (PROVIDER_TELEGRAM, 'Telegram Stars'),
    ]
    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES, default=PROVIDER_PADDLE)

    paddle_subscription_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    paddle_customer_id = models.CharField(max_length=64, blank=True)
    tg_payment_charge_id = models.CharField(max_length=128, blank=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'status'])]

    def is_active(self) -> bool:
        return self.status in (self.STATUS_ACTIVE, self.STATUS_TRIALING)


class Entitlement(models.Model):
    """Per-user feature unlock — derived from active subscription or credit purchase.

    A user can have many entitlement rows (one per key). Permission checks read here.
    Keys are free-form strings agreed with frontend: 'premium_spreads', 'sonnet_ai',
    'celtic_cross', 'natal_chart', etc.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entitlements',
    )
    key = models.CharField(max_length=64)
    expires_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'key')
        indexes = [models.Index(fields=['user', 'key'])]

    def is_valid(self) -> bool:
        from django.utils import timezone
        if self.expires_at is None:
            return True
        return self.expires_at > timezone.now()


class CreditWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credit_wallet',
    )
    balance = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.user_id}: {self.balance} credits'


class UsageLedger(models.Model):
    """Append-only log. Negative cost = grant (subscription tick or pack purchase)."""
    KIND_AI_TAROT = 'ai_tarot'
    KIND_AI_RUNES = 'ai_runes'
    KIND_AI_DEEP = 'ai_deep'
    KIND_GRANT_SUB = 'grant_subscription'
    KIND_GRANT_PACK = 'grant_pack'
    KIND_CHOICES = [
        (KIND_AI_TAROT, 'AI tarot reading'),
        (KIND_AI_RUNES, 'AI rune cast'),
        (KIND_AI_DEEP, 'AI deep reading'),
        (KIND_GRANT_SUB, 'Subscription monthly grant'),
        (KIND_GRANT_PACK, 'Credit pack purchase'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_ledger',
    )
    kind = models.CharField(max_length=24, choices=KIND_CHOICES)
    cost_credits = models.IntegerField()
    model_used = models.CharField(max_length=64, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    reference_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]


class PaddleEvent(models.Model):
    """Idempotency record. Webhook handler insert-or-skip by event_id."""
    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=64)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)
