"""Entitlement gating + credit deduction logic."""
import pytest

from apps.billing import services as billing
from apps.billing.models import CreditWallet, Entitlement, Subscription, UsageLedger, Plan


@pytest.fixture
def user(django_user_model, db):
    return django_user_model.objects.create_user(
        username='bob', email='bob@example.com', password='pw',
    )


@pytest.fixture
def free_user(user):
    return user


@pytest.fixture
def premium_user(user, db):
    Entitlement.objects.create(user=user, key='sonnet_ai')
    CreditWallet.objects.create(user=user, balance=50)
    return user


@pytest.mark.django_db
class TestTier:
    def test_anonymous_is_free(self):
        info = billing.tier_for(None)
        assert info.tier == 'free'

    def test_no_entitlements_is_free(self, free_user):
        assert billing.tier_for(free_user).tier == 'free'

    def test_sonnet_entitlement_is_premium(self, premium_user):
        info = billing.tier_for(premium_user)
        assert info.tier == 'premium'
        assert 'sonnet_ai' in info.entitlements


@pytest.mark.django_db
class TestCharge:
    def test_premium_with_credits_deducts(self, premium_user):
        charged, balance = billing.charge_credits(
            user=premium_user, kind=UsageLedger.KIND_AI_TAROT,
        )
        assert charged is True
        assert balance == 49
        assert UsageLedger.objects.filter(user=premium_user).count() == 1

    def test_free_user_without_credits_is_blocked(self, free_user):
        charged, balance = billing.charge_credits(
            user=free_user, kind=UsageLedger.KIND_AI_TAROT,
        )
        assert charged is False
        assert balance == 0

    def test_premium_with_zero_credits_still_allowed(self, premium_user):
        CreditWallet.objects.filter(user=premium_user).update(balance=0)
        charged, balance = billing.charge_credits(
            user=premium_user, kind=UsageLedger.KIND_AI_TAROT,
        )
        # Premium has an implicit allowance — but balance stays 0.
        assert charged is True
        assert balance == 0


@pytest.mark.django_db
class TestSubscriptionApply:
    def test_activate_creates_entitlements_and_grants_credits(self, free_user):
        plan = Plan.objects.create(
            slug='premium-monthly',
            name_ru='Premium', name_en='Premium',
            kind=Plan.KIND_SUBSCRIPTION,
            monthly_included_credits=50,
            entitlement_keys=['sonnet_ai', 'celtic_cross'],
        )
        sub = billing.apply_subscription_activated(
            user=free_user, plan=plan, paddle_subscription_id='sub_X',
        )
        assert sub.status == Subscription.STATUS_ACTIVE
        keys = set(Entitlement.objects.filter(user=free_user).values_list('key', flat=True))
        assert keys == {'sonnet_ai', 'celtic_cross'}
        assert CreditWallet.objects.get(user=free_user).balance == 50

    def test_activate_is_idempotent_for_same_paddle_id(self, free_user):
        plan = Plan.objects.create(
            slug='premium-monthly',
            name_ru='Premium', name_en='Premium',
            kind=Plan.KIND_SUBSCRIPTION,
            monthly_included_credits=50,
            entitlement_keys=['sonnet_ai'],
        )
        billing.apply_subscription_activated(user=free_user, plan=plan, paddle_subscription_id='sub_X')
        billing.apply_subscription_activated(user=free_user, plan=plan, paddle_subscription_id='sub_X')
        # Credits will accumulate on each call (one grant per activation).
        # That's fine for renewals; the webhook idempotency guard prevents
        # accidental double-grants from duplicate deliveries.
        assert Subscription.objects.filter(paddle_subscription_id='sub_X').count() == 1
        # Two activations → two grants.
        assert CreditWallet.objects.get(user=free_user).balance == 100
