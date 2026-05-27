"""
Tests for Telegram Stars billing flow:

1. telegram_checkout — POST /api/v1/billing/checkout/telegram/
   Generates a t.me deep-link with a signed payment token.

2. telegram_invoice — POST /api/v1/billing/checkout/telegram-invoice/
   Creates an invoice link via Telegram Bot API (mocked).

3. apply_tg_payment (service layer)
   Activates subscription / grants credits after Stars payment succeeds.

4. Celtic Cross premium gating
   Creating a celtic-cross reading is blocked without 'celtic_cross' entitlement.
"""
import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient

from apps.billing.models import (
    CreditWallet,
    Entitlement,
    Plan,
    Subscription,
)
from apps.billing import services as billing


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def user(django_user_model, db):
    return django_user_model.objects.create_user(
        username='tg_pay_user',
        email='tg@example.com',
        password='pw',
    )


@pytest.fixture
def premium_plan(db):
    return Plan.objects.create(
        slug='premium-monthly',
        name_ru='Premium',
        name_en='Premium',
        description_ru='AI-расклады',
        description_en='AI readings',
        kind=Plan.KIND_SUBSCRIPTION,
        tg_stars_price=250,
        monthly_included_credits=50,
        entitlement_keys=['sonnet_ai', 'celtic_cross', 'runes_ai'],
        is_active=True,
    )


@pytest.fixture
def credits_plan(db):
    return Plan.objects.create(
        slug='credits-small',
        name_ru='10 кредитов',
        name_en='10 credits',
        description_ru='Пак кредитов',
        description_en='Credit pack',
        kind=Plan.KIND_CREDITS,
        tg_stars_price=75,
        credits_granted=10,
        entitlement_keys=[],
        is_active=True,
    )


@pytest.fixture
def free_plan(db):
    return Plan.objects.create(
        slug='free',
        name_ru='Бесплатный',
        name_en='Free',
        description_ru='Бесплатно',
        description_en='Free',
        kind=Plan.KIND_FREE,
        tg_stars_price=0,
        is_active=True,
    )


# ── telegram_checkout tests ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTelegramCheckout:
    URL = '/api/v1/billing/checkout/telegram/'

    def test_unauthenticated_returns_401(self, api, premium_plan):
        resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')
        assert resp.status_code == 401

    def test_missing_plan_slug_returns_400(self, api, user):
        api.force_authenticate(user=user)
        resp = api.post(self.URL, {}, format='json')
        assert resp.status_code == 400

    def test_unknown_plan_returns_404(self, api, user):
        api.force_authenticate(user=user)
        resp = api.post(self.URL, {'plan_slug': 'nonexistent'}, format='json')
        assert resp.status_code == 404

    def test_free_plan_returns_400(self, api, user, free_plan):
        api.force_authenticate(user=user)
        resp = api.post(self.URL, {'plan_slug': 'free'}, format='json')
        assert resp.status_code == 400

    def test_plan_without_stars_price_returns_503(self, api, user, db):
        Plan.objects.create(
            slug='no-stars',
            name_ru='No Stars',
            name_en='No Stars',
            kind=Plan.KIND_SUBSCRIPTION,
            tg_stars_price=0,
            is_active=True,
        )
        api.force_authenticate(user=user)
        resp = api.post(self.URL, {'plan_slug': 'no-stars'}, format='json')
        assert resp.status_code == 503

    def test_valid_premium_plan_returns_tg_link(self, api, user, premium_plan, settings):
        settings.TELEGRAM_BOT_TOKEN = 'test_token'
        settings.TELEGRAM_BOT_USERNAME = 'test_bot'
        settings.TELEGRAM_PAYMENT_SECRET = 'a' * 64
        api.force_authenticate(user=user)

        resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')

        assert resp.status_code == 200
        assert 'url' in resp.data
        assert resp.data['url'].startswith('https://t.me/test_bot?start=buy_')
        assert resp.data['stars'] == 250
        assert resp.data['plan']['slug'] == 'premium-monthly'


# ── telegram_invoice tests ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTelegramInvoice:
    URL = '/api/v1/billing/checkout/telegram-invoice/'

    def test_unauthenticated_returns_401(self, api, premium_plan):
        resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')
        assert resp.status_code == 401

    def test_missing_plan_slug_returns_400(self, api, user):
        api.force_authenticate(user=user)
        resp = api.post(self.URL, {}, format='json')
        assert resp.status_code == 400

    def test_telegram_not_configured_returns_503(self, api, user, premium_plan, settings):
        settings.TELEGRAM_BOT_TOKEN = ''
        api.force_authenticate(user=user)
        resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')
        assert resp.status_code == 503

    def test_tg_api_success_returns_invoice_link(self, api, user, premium_plan, settings):
        settings.TELEGRAM_BOT_TOKEN = 'fake_token'

        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True, 'result': 'https://t.me/$invoice_abc'}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_response):
            api.force_authenticate(user=user)
            resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')

        assert resp.status_code == 200
        assert resp.data['invoice_link'] == 'https://t.me/$invoice_abc'
        assert resp.data['stars'] == 250

    def test_tg_api_error_returns_502(self, api, user, premium_plan, settings):
        settings.TELEGRAM_BOT_TOKEN = 'fake_token'

        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': False, 'description': 'Bad Request'}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_response):
            api.force_authenticate(user=user)
            resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')

        assert resp.status_code == 502

    def test_tg_api_network_error_returns_502(self, api, user, premium_plan, settings):
        settings.TELEGRAM_BOT_TOKEN = 'fake_token'

        with patch('requests.post', side_effect=Exception('timeout')):
            api.force_authenticate(user=user)
            resp = api.post(self.URL, {'plan_slug': 'premium-monthly'}, format='json')

        assert resp.status_code == 502


# ── apply_tg_payment service tests ────────────────────────────────────────────

@pytest.mark.django_db
class TestApplyTgPayment:
    def test_subscription_creates_sub_and_entitlements(self, user, premium_plan):
        billing.apply_tg_payment(user=user, plan=premium_plan, charge_id='charge_001')

        sub = Subscription.objects.get(user=user, tg_payment_charge_id='charge_001')
        assert sub.status == Subscription.STATUS_ACTIVE
        assert sub.provider == Subscription.PROVIDER_TELEGRAM

        keys = set(Entitlement.objects.filter(user=user).values_list('key', flat=True))
        assert 'sonnet_ai' in keys
        assert 'celtic_cross' in keys
        assert 'runes_ai' in keys

        wallet = CreditWallet.objects.get(user=user)
        assert wallet.balance == 50  # monthly_included_credits

    def test_subscription_idempotent_by_charge_id(self, user, premium_plan):
        billing.apply_tg_payment(user=user, plan=premium_plan, charge_id='charge_idem')
        billing.apply_tg_payment(user=user, plan=premium_plan, charge_id='charge_idem')

        assert Subscription.objects.filter(
            user=user, tg_payment_charge_id='charge_idem'
        ).count() == 1

    def test_credits_pack_grants_credits(self, user, credits_plan):
        billing.apply_tg_payment(user=user, plan=credits_plan, charge_id='charge_credits_1')

        wallet = CreditWallet.objects.get(user=user)
        assert wallet.balance == 10  # credits_granted

        # No subscription created for credit packs
        assert Subscription.objects.filter(user=user).count() == 0

    def test_credits_pack_accumulates_on_multiple_purchases(self, user, credits_plan):
        billing.apply_tg_payment(user=user, plan=credits_plan, charge_id='charge_c1')
        billing.apply_tg_payment(user=user, plan=credits_plan, charge_id='charge_c2')

        wallet = CreditWallet.objects.get(user=user)
        assert wallet.balance == 20


# ── Celtic Cross premium gating tests ─────────────────────────────────────────

@pytest.mark.django_db
class TestCelticCrossGating:
    """
    Celtic Cross spread requires the 'celtic_cross' entitlement.
    Anonymous and free-tier users should get 403.
    """

    SPREADS_URL = '/api/v1/readings/'

    def _create_10_cards(self, db):
        from apps.tarot.models import Card, SpreadType
        cards = []
        for i in range(10):
            cards.append(
                Card.objects.create(
                    slug=f'cc-card-{i}',
                    suit='major',
                    number=i,
                    name_ru=f'Карта {i}',
                    name_en=f'Card {i}',
                    upright_meaning_ru='значение',
                    upright_meaning_en='meaning',
                    reversed_meaning_ru='обратное',
                    reversed_meaning_en='reversed',
                    keywords_ru=['ключ'],
                    keywords_en=['key'],
                    image_url=f'/cards/cc-{i}.jpg',
                )
            )
        SpreadType.objects.create(
            slug='celtic-cross',
            name_ru='Кельтский крест',
            name_en='Celtic Cross',
            positions_count=10,
            positions=[
                {'index': i, 'label_ru': f'Позиция {i}', 'label_en': f'Position {i}',
                 'meaning_ru': 'смысл', 'meaning_en': 'meaning'}
                for i in range(10)
            ],
        )
        return cards

    def test_anonymous_user_cannot_create_celtic_cross(self, api, db):
        self._create_10_cards(db)
        resp = api.post(self.SPREADS_URL, {
            'spread_slug': 'celtic-cross',
            'locale': 'en',
        }, format='json')
        assert resp.status_code in (401, 403)

    def test_free_user_cannot_create_celtic_cross(self, api, user, db):
        self._create_10_cards(db)
        api.force_authenticate(user=user)
        resp = api.post(self.SPREADS_URL, {
            'spread_slug': 'celtic-cross',
            'locale': 'en',
        }, format='json')
        assert resp.status_code == 403
        assert resp.data.get('detail') == 'premium_required'

    def test_premium_user_can_create_celtic_cross(self, api, user, db):
        self._create_10_cards(db)
        Entitlement.objects.create(user=user, key='celtic_cross')
        api.force_authenticate(user=user)
        resp = api.post(self.SPREADS_URL, {
            'spread_slug': 'celtic-cross',
            'locale': 'en',
        }, format='json')
        # 201 Created — reading drawn successfully
        assert resp.status_code == 201
        assert resp.data['spread_type']['slug'] == 'celtic-cross'
        assert len(resp.data['cards']) == 10
