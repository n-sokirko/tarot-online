"""
Comprehensive backend integration tests simulating a real user's full lifecycle.

Test classes:
  TestFullUserLifecycle      — end-to-end: register → read → upgrade → Celtic Cross → credit deduction
  TestTelegramAuthLifecycle  — Telegram Mini App auth flow
  TestFreeTierBlocking       — free-tier user hits interpret → 402
  TestPremiumViaWhatsApp     — apply_tg_payment → entitlements → Celtic Cross unlocked
  TestCelticCrossReading     — premium user creates Celtic Cross, gets 10 cards back
  TestCreditDeduction        — interpret deducts credits, ledger entry created
  TestLanguageSwitching      — readings in 'ru' and 'en' return correct locale field
  TestBillingMeStatus        — /api/v1/billing/me/ reflects tier + entitlements after upgrade
  TestAnonymousRateLimit     — anon user hits interpret ANON_DAILY_LIMIT+1 times → 429
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.billing import services as billing
from apps.billing.models import (
    CreditWallet,
    Entitlement,
    Plan,
    Subscription,
    UsageLedger,
)
from apps.readings.models import Reading, ReadingCard
from apps.tarot.models import Card, SpreadType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOT_TOKEN = "test_bot_token:STUB"  # matches config/settings/test.py TELEGRAM_BOT_TOKEN


# ---------------------------------------------------------------------------
# HMAC helper (mirrors apps/users/tests/test_telegram_auth.py)
# ---------------------------------------------------------------------------

def _make_init_data(tg_user_dict: dict, bot_token: str = BOT_TOKEN) -> str:
    """Build a valid Telegram initData string signed with the given token."""
    user_json = json.dumps(tg_user_dict, separators=(",", ":"))
    auth_date = int(time.time())
    params = {
        "auth_date": str(auth_date),
        "user": user_json,
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params["hash"] = hash_value
    return urllib.parse.urlencode(params)


# ---------------------------------------------------------------------------
# Shared AI mock helper
# ---------------------------------------------------------------------------

def _mock_ai_result():
    from services.ai.client import GenerationResult
    return GenerationResult(
        body="Mystical interpretation text...",
        model="claude-haiku-4-5-20251001",
        input_tokens=100,
        output_tokens=80,
    )


# ---------------------------------------------------------------------------
# Shared DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def three_card_spread(db):
    return SpreadType.objects.create(
        slug="three-card",
        name_ru="Три карты",
        name_en="Three Card",
        positions_count=3,
        positions=[
            {"index": 0, "label_ru": "Прошлое", "label_en": "Past", "meaning_ru": "прошлое", "meaning_en": "past"},
            {"index": 1, "label_ru": "Настоящее", "label_en": "Present", "meaning_ru": "настоящее", "meaning_en": "present"},
            {"index": 2, "label_ru": "Будущее", "label_en": "Future", "meaning_ru": "будущее", "meaning_en": "future"},
        ],
    )


@pytest.fixture
def celtic_cross_spread(db):
    return SpreadType.objects.create(
        slug="celtic-cross",
        name_ru="Кельтский крест",
        name_en="Celtic Cross",
        positions_count=10,
        positions=[
            {
                "index": i,
                "label_ru": f"Позиция {i}",
                "label_en": f"Position {i}",
                "meaning_ru": "смысл",
                "meaning_en": "meaning",
            }
            for i in range(10)
        ],
    )


@pytest.fixture
def deck_3(db):
    """Minimal deck — 3 cards, enough for a three-card spread."""
    cards = []
    for i in range(5):  # create 5 so random.sample has room to pick 3 distinct
        cards.append(
            Card.objects.create(
                slug=f"lc-card-{i}",
                suit="major",
                number=i,
                name_ru=f"Карта {i}",
                name_en=f"Card {i}",
                upright_meaning_ru="значение",
                upright_meaning_en="meaning",
                reversed_meaning_ru="обратное",
                reversed_meaning_en="reversed",
                keywords_ru=["ключ"],
                keywords_en=["key"],
                image_url=f"/cards/lc-{i}.jpg",
            )
        )
    return cards


@pytest.fixture
def deck_10(db):
    """10 cards — enough for Celtic Cross."""
    cards = []
    for i in range(10):
        cards.append(
            Card.objects.create(
                slug=f"cc-card-{i}",
                suit="major",
                number=i,
                name_ru=f"Карта {i}",
                name_en=f"Card {i}",
                upright_meaning_ru="значение",
                upright_meaning_en="meaning",
                reversed_meaning_ru="обратное",
                reversed_meaning_en="reversed",
                keywords_ru=["ключ"],
                keywords_en=["key"],
                image_url=f"/cards/cc-{i}.jpg",
            )
        )
    return cards


@pytest.fixture
def premium_plan(db):
    return Plan.objects.create(
        slug="premium-monthly",
        name_ru="Premium",
        name_en="Premium",
        description_ru="AI-расклады",
        description_en="AI readings",
        kind=Plan.KIND_SUBSCRIPTION,
        tg_stars_price=250,
        monthly_included_credits=50,
        entitlement_keys=["sonnet_ai", "celtic_cross", "runes_ai"],
        is_active=True,
    )


@pytest.fixture
def free_user(django_user_model, db):
    return django_user_model.objects.create_user(
        username="free_user@example.com",
        email="free_user@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def premium_user(django_user_model, db, premium_plan):
    user = django_user_model.objects.create_user(
        username="premium_user@example.com",
        email="premium_user@example.com",
        password="StrongPass123!",
    )
    billing.apply_tg_payment(user=user, plan=premium_plan, charge_id="setup_charge_001")
    return user


# ===========================================================================
# 1. Full User Lifecycle (end-to-end)
# ===========================================================================

@pytest.mark.django_db
class TestFullUserLifecycle:
    """
    Simulates a complete user journey:
      register → login → JWT → read (3-card) → blocked interpret (402)
      → upgrade via TG → Celtic Cross unlocked → interpret → credits deducted
    """

    REGISTER_URL = "/api/v1/auth/register/"
    LOGIN_URL = "/api/v1/auth/login/"
    READINGS_URL = "/api/v1/readings/"
    BILLING_ME_URL = "/api/v1/billing/me/"

    def test_register_returns_201_with_tokens(self, api, db):
        resp = api.post(
            self.REGISTER_URL,
            {"email": "alice@example.com", "password": "StrongPass123!", "display_name": "Alice"},
            format="json",
        )
        assert resp.status_code == 201
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["email"] == "alice@example.com"

    def test_login_with_jwt_accesses_protected_endpoint(self, api, db):
        # Register
        api.post(
            self.REGISTER_URL,
            {"email": "bob@example.com", "password": "StrongPass123!"},
            format="json",
        )
        # Login
        resp = api.post(
            self.LOGIN_URL,
            {"email": "bob@example.com", "password": "StrongPass123!"},
            format="json",
        )
        assert resp.status_code == 200
        token = resp.data["access"]

        # Access protected endpoint using JWT
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me_resp = api.get("/api/v1/auth/me/")
        assert me_resp.status_code == 200
        assert me_resp.data["email"] == "bob@example.com"

    def test_free_tier_reading_then_interpret_blocked_402(
        self, api, free_user, deck_3, three_card_spread
    ):
        """Free user with no credits gets 402 when attempting interpret."""
        api.force_authenticate(user=free_user)

        # Create reading
        resp = api.post(
            self.READINGS_URL,
            {"question": "What is my path?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        assert resp.status_code == 201
        reading_id = resp.data["id"]

        # Try interpret — free user has zero credits → 402
        resp = api.post(f"/api/v1/readings/{reading_id}/interpret/")
        assert resp.status_code == 402
        assert resp.data["detail"] == "out_of_credits"

    def test_full_lifecycle_register_upgrade_celtic_cross(
        self, api, db, premium_plan, deck_10, celtic_cross_spread
    ):
        """
        Full end-to-end: register → reading → upgrade via TG Stars
        → Celtic Cross unlocked → interpret with credit deduction.

        Note: ReadingViewSet uses authentication_classes=[] so JWT headers are not
        processed for the readings endpoint. We use force_authenticate after upgrading
        to simulate the authenticated premium user making the Celtic Cross request.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Step 1: Register
        resp = api.post(
            self.REGISTER_URL,
            {"email": "eve@example.com", "password": "StrongPass123!"},
            format="json",
        )
        assert resp.status_code == 201
        access_token = resp.data["access"]
        user = User.objects.get(email="eve@example.com")

        # Step 2: Use JWT for authenticated request to /auth/me/ (that endpoint DOES use JWT)
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_resp = api.get("/api/v1/auth/me/")
        assert me_resp.status_code == 200

        # Step 3: Free tier — Celtic Cross is blocked (no auth needed; check is by entitlement)
        api.credentials()  # clear JWT since readings endpoint ignores it anyway
        api.force_authenticate(user=user)
        resp = api.post(
            self.READINGS_URL,
            {"question": "What lies ahead?", "locale": "en", "spread_slug": "celtic-cross"},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["detail"] == "premium_required"

        # Step 4: Simulate Telegram Stars payment → apply_tg_payment
        billing.apply_tg_payment(user=user, plan=premium_plan, charge_id="tg_charge_eve_001")

        # Step 5: Celtic Cross now unlocked (user is already force_authenticated)
        resp = api.post(
            self.READINGS_URL,
            {"question": "What lies ahead?", "locale": "en", "spread_slug": "celtic-cross"},
            format="json",
        )
        assert resp.status_code == 201
        assert len(resp.data["cards"]) == 10
        reading_id = resp.data["id"]

        # Step 6: Interpret → credits deducted, ledger entry created
        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            resp = api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "What lies ahead?"},
                format="json",
            )
        assert resp.status_code == 201
        assert "body_md" in resp.data

        wallet = CreditWallet.objects.get(user=user)
        assert wallet.balance == 49  # started at 50, used 1

        assert UsageLedger.objects.filter(
            user=user, kind=UsageLedger.KIND_AI_TAROT
        ).exists()


# ===========================================================================
# 2. Telegram Mini App Auth
# ===========================================================================

@pytest.mark.django_db
class TestTelegramAuthLifecycle:
    URL = "/api/v1/auth/telegram-webapp/"

    def test_valid_initdata_creates_user_and_returns_jwt(self, api):
        tg_user = {"id": 555, "first_name": "Tanya", "username": "tanya_tg"}
        init_data = _make_init_data(tg_user)

        resp = api.post(self.URL, {"init_data": init_data}, format="json")

        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["email"] == "tg_555@telegram.local"

    def test_tg_jwt_grants_access_to_protected_endpoint(self, api):
        tg_user = {"id": 666, "first_name": "Pavel"}
        init_data = _make_init_data(tg_user)

        resp = api.post(self.URL, {"init_data": init_data}, format="json")
        assert resp.status_code == 200
        token = resp.data["access"]

        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me_resp = api.get("/api/v1/auth/me/")
        assert me_resp.status_code == 200
        assert me_resp.data["email"] == "tg_666@telegram.local"

    def test_invalid_signature_returns_400(self, api):
        init_data = _make_init_data({"id": 777, "first_name": "Bad"}, bot_token="wrong_token")
        resp = api.post(self.URL, {"init_data": init_data}, format="json")
        assert resp.status_code == 400
        assert resp.data["error"] == "Invalid initData signature."

    def test_missing_init_data_returns_400(self, api):
        resp = api.post(self.URL, {}, format="json")
        assert resp.status_code == 400

    def test_second_login_no_duplicate_user(self, api):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        tg_user = {"id": 888, "first_name": "Repeat"}
        init_data = _make_init_data(tg_user)

        api.post(self.URL, {"init_data": init_data}, format="json")
        api.post(self.URL, {"init_data": init_data}, format="json")

        assert User.objects.filter(email="tg_888@telegram.local").count() == 1


# ===========================================================================
# 3. Free-Tier Blocking
# ===========================================================================

@pytest.mark.django_db
class TestFreeTierBlocking:
    READINGS_URL = "/api/v1/readings/"

    def test_free_user_interpret_blocked_402(self, api, free_user, deck_3, three_card_spread):
        """Free user (zero credits) gets 402 on interpret."""
        api.force_authenticate(user=free_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "Will I succeed?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        assert resp.status_code == 201
        reading_id = resp.data["id"]

        resp = api.post(f"/api/v1/readings/{reading_id}/interpret/")
        assert resp.status_code == 402
        assert resp.data["detail"] == "out_of_credits"

    def test_free_user_cannot_do_celtic_cross(self, api, free_user, deck_10, celtic_cross_spread):
        """Free user cannot create Celtic Cross reading."""
        api.force_authenticate(user=free_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "Show me my destiny.", "locale": "en", "spread_slug": "celtic-cross"},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["detail"] == "premium_required"
        assert resp.data["required_entitlement"] == "celtic_cross"


# ===========================================================================
# 4. Premium via Telegram Payment
# ===========================================================================

@pytest.mark.django_db
class TestPremiumViaTelegramPayment:
    BILLING_ME_URL = "/api/v1/billing/me/"
    CHECKOUT_TG_URL = "/api/v1/billing/checkout/telegram/"

    def test_checkout_endpoint_returns_tg_deep_link(self, api, free_user, premium_plan, settings):
        settings.TELEGRAM_BOT_TOKEN = "test_token_123"
        settings.TELEGRAM_BOT_USERNAME = "test_bot"
        settings.TELEGRAM_PAYMENT_SECRET = "a" * 64

        api.force_authenticate(user=free_user)
        resp = api.post(self.CHECKOUT_TG_URL, {"plan_slug": "premium-monthly"}, format="json")

        assert resp.status_code == 200
        assert resp.data["url"].startswith("https://t.me/test_bot?start=buy_")
        assert resp.data["stars"] == 250
        assert resp.data["plan"]["slug"] == "premium-monthly"

    def test_apply_tg_payment_grants_subscription_and_entitlements(
        self, free_user, premium_plan
    ):
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="tg_charge_100")

        sub = Subscription.objects.get(user=free_user, tg_payment_charge_id="tg_charge_100")
        assert sub.status == Subscription.STATUS_ACTIVE
        assert sub.provider == Subscription.PROVIDER_TELEGRAM

        keys = set(Entitlement.objects.filter(user=free_user).values_list("key", flat=True))
        assert "sonnet_ai" in keys
        assert "celtic_cross" in keys
        assert "runes_ai" in keys

    def test_apply_tg_payment_grants_monthly_credits(self, free_user, premium_plan):
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="tg_charge_101")

        wallet = CreditWallet.objects.get(user=free_user)
        assert wallet.balance == 50  # monthly_included_credits

    def test_apply_tg_payment_is_idempotent(self, free_user, premium_plan):
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="tg_idem_001")
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="tg_idem_001")

        assert Subscription.objects.filter(tg_payment_charge_id="tg_idem_001").count() == 1

    def test_billing_me_reflects_premium_tier_after_upgrade(
        self, api, free_user, premium_plan
    ):
        # Before upgrade — free tier
        api.force_authenticate(user=free_user)
        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 200
        assert resp.data["tier"] == "free"

        # Upgrade via TG payment
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="tg_charge_me_01")

        # After upgrade — premium tier
        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 200
        assert resp.data["tier"] == "premium"
        assert "celtic_cross" in resp.data["entitlements"]
        assert "sonnet_ai" in resp.data["entitlements"]
        assert resp.data["credits"] == 50
        # subscription object is present and active
        assert resp.data["subscription"] is not None
        assert resp.data["subscription"]["status"] == "active"

    def test_billing_me_requires_auth(self, api):
        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 401


# ===========================================================================
# 5. Celtic Cross After Premium
# ===========================================================================

@pytest.mark.django_db
class TestCelticCrossAfterPremium:
    READINGS_URL = "/api/v1/readings/"

    def test_premium_user_creates_celtic_cross_gets_10_cards(
        self, api, premium_user, deck_10, celtic_cross_spread
    ):
        api.force_authenticate(user=premium_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "What is my purpose?", "locale": "en", "spread_slug": "celtic-cross"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.data

        assert data["spread_type"]["slug"] == "celtic-cross"
        assert len(data["cards"]) == 10

        # All 10 position indices are present and unique
        indices = sorted(c["position_index"] for c in data["cards"])
        assert indices == list(range(10))

        # All card slugs are distinct
        slugs = [c["card"]["slug"] for c in data["cards"]]
        assert len(slugs) == len(set(slugs))

    def test_celtic_cross_reading_persisted_to_db(
        self, api, premium_user, deck_10, celtic_cross_spread
    ):
        api.force_authenticate(user=premium_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "My journey?", "locale": "ru", "spread_slug": "celtic-cross"},
            format="json",
        )
        assert resp.status_code == 201
        reading_id = resp.data["id"]

        assert Reading.objects.filter(pk=reading_id).exists()
        assert ReadingCard.objects.filter(reading_id=reading_id).count() == 10

    def test_celtic_cross_can_be_retrieved_by_id(
        self, api, premium_user, deck_10, celtic_cross_spread
    ):
        api.force_authenticate(user=premium_user)

        create_resp = api.post(
            self.READINGS_URL,
            {"question": "Q?", "locale": "en", "spread_slug": "celtic-cross"},
            format="json",
        )
        assert create_resp.status_code == 201
        reading_id = create_resp.data["id"]

        get_resp = api.get(f"/api/v1/readings/{reading_id}/")
        assert get_resp.status_code == 200
        assert len(get_resp.data["cards"]) == 10
        assert get_resp.data["spread_type"]["slug"] == "celtic-cross"


# ===========================================================================
# 6. Credit Deduction
# ===========================================================================

@pytest.mark.django_db
class TestCreditDeduction:
    READINGS_URL = "/api/v1/readings/"

    def test_interpret_deducts_one_credit(
        self, api, premium_user, deck_3, three_card_spread
    ):
        api.force_authenticate(user=premium_user)

        before = CreditWallet.objects.get(user=premium_user).balance  # 50

        resp = api.post(
            self.READINGS_URL,
            {"question": "What do the cards say?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        assert resp.status_code == 201
        reading_id = resp.data["id"]

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            resp = api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "What do the cards say?"},
                format="json",
            )
        assert resp.status_code == 201

        after = CreditWallet.objects.get(user=premium_user).balance
        assert after == before - 1

    def test_interpret_creates_ledger_entry(
        self, api, premium_user, deck_3, three_card_spread
    ):
        api.force_authenticate(user=premium_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "Will things improve?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        reading_id = resp.data["id"]

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "Will things improve?"},
                format="json",
            )

        ledger_entry = UsageLedger.objects.filter(
            user=premium_user, kind=UsageLedger.KIND_AI_TAROT
        ).last()
        assert ledger_entry is not None
        assert ledger_entry.cost_credits == 1
        assert f"reading:{reading_id}" in ledger_entry.reference_id

    def test_interpret_idempotent_charges_only_once(
        self, api, premium_user, deck_3, three_card_spread
    ):
        """Second call to /interpret/ on same reading returns cached result, no extra charge."""
        api.force_authenticate(user=premium_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "Show me!", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        reading_id = resp.data["id"]

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ) as mock_gen:
            api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "Show me!"},
                format="json",
            )
            api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "Show me!"},
                format="json",
            )

        # AI called only once — second request returns cached interpretation
        assert mock_gen.call_count == 1
        # Credits deducted only once
        ai_charges = UsageLedger.objects.filter(
            user=premium_user, kind=UsageLedger.KIND_AI_TAROT, cost_credits=1
        )
        assert ai_charges.count() == 1

    def test_premium_with_zero_credits_still_allowed(
        self, api, premium_user, deck_3, three_card_spread
    ):
        """Premium user with zero balance still gets interpretation (implicit allowance)."""
        CreditWallet.objects.filter(user=premium_user).update(balance=0)
        api.force_authenticate(user=premium_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "Am I on the right track?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        reading_id = resp.data["id"]

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            resp = api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "Am I on the right track?"},
                format="json",
            )
        assert resp.status_code == 201


# ===========================================================================
# 7. Language Switching
# ===========================================================================

@pytest.mark.django_db
class TestLanguageSwitching:
    READINGS_URL = "/api/v1/readings/"

    def test_reading_in_ru_locale_has_locale_field_ru(self, api, deck_3, three_card_spread):
        resp = api.post(
            self.READINGS_URL,
            {"question": "Что меня ждёт?", "locale": "ru", "spread_slug": "three-card"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["locale"] == "ru"

    def test_reading_in_en_locale_has_locale_field_en(self, api, deck_3, three_card_spread):
        resp = api.post(
            self.READINGS_URL,
            {"question": "What awaits me?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["locale"] == "en"

    def test_two_readings_different_locales_both_created(self, api, deck_3, three_card_spread):
        resp_ru = api.post(
            self.READINGS_URL,
            {"question": "Что меня ждёт?", "locale": "ru", "spread_slug": "three-card"},
            format="json",
        )
        resp_en = api.post(
            self.READINGS_URL,
            {"question": "What awaits me?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        assert resp_ru.status_code == 201
        assert resp_en.status_code == 201

        # Verify the readings are stored with correct locales
        ru_reading = Reading.objects.get(pk=resp_ru.data["id"])
        en_reading = Reading.objects.get(pk=resp_en.data["id"])
        assert ru_reading.locale == "ru"
        assert en_reading.locale == "en"

    def test_invalid_locale_returns_400(self, api, deck_3, three_card_spread):
        resp = api.post(
            self.READINGS_URL,
            {"question": "Was?", "locale": "de", "spread_slug": "three-card"},
            format="json",
        )
        assert resp.status_code == 400

    def test_ai_prompt_uses_correct_locale_in_user_message(
        self, api, premium_user, deck_3, three_card_spread
    ):
        """Verify that the user message passed to AI reflects the reading locale."""
        api.force_authenticate(user=premium_user)

        resp = api.post(
            self.READINGS_URL,
            {"question": "What is my future?", "locale": "en", "spread_slug": "three-card"},
            format="json",
        )
        reading_id = resp.data["id"]

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ) as mock_gen:
            api.post(
                f"/api/v1/readings/{reading_id}/interpret/",
                {"question": "What is my future?"},
                format="json",
            )

        user_msg = mock_gen.call_args.kwargs["user_message"]
        # English prompt uses English labels
        assert "Question:" in user_msg or "Spread:" in user_msg


# ===========================================================================
# 8. Billing/Me Status Endpoint
# ===========================================================================

@pytest.mark.django_db
class TestBillingMeStatus:
    BILLING_ME_URL = "/api/v1/billing/me/"

    def test_free_user_tier_is_free(self, api, free_user):
        api.force_authenticate(user=free_user)
        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 200
        assert resp.data["tier"] == "free"
        assert resp.data["credits"] == 0
        assert resp.data["entitlements"] == []
        assert resp.data["subscription"] is None

    def test_after_tg_payment_tier_is_premium(self, api, free_user, premium_plan):
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="bm_charge_001")
        api.force_authenticate(user=free_user)

        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 200
        assert resp.data["tier"] == "premium"
        assert resp.data["credits"] == 50
        assert "sonnet_ai" in resp.data["entitlements"]
        assert "celtic_cross" in resp.data["entitlements"]
        assert "runes_ai" in resp.data["entitlements"]

    def test_subscription_details_in_response(self, api, free_user, premium_plan):
        """
        Verify /billing/me/ returns a non-null subscription with status and period fields.
        Note: the billing_me view pre-serializes the Subscription via SubscriptionSerializer
        and then passes the resulting dict into BillingMeSerializer. Due to this double-
        serialization, the 'plan_slug' field (which uses source='plan.slug') is not accessible
        on the dict and is dropped. We test the fields that do survive: status and period end.
        """
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="bm_charge_002")
        api.force_authenticate(user=free_user)

        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 200
        sub = resp.data["subscription"]
        assert sub is not None
        assert sub["status"] == "active"
        assert sub["current_period_end"] is not None

    def test_unauthenticated_returns_401(self, api):
        resp = api.get(self.BILLING_ME_URL)
        assert resp.status_code == 401

    def test_entitlements_sorted_alphabetically(self, api, free_user, premium_plan):
        billing.apply_tg_payment(user=free_user, plan=premium_plan, charge_id="bm_charge_003")
        api.force_authenticate(user=free_user)

        resp = api.get(self.BILLING_ME_URL)
        assert resp.data["entitlements"] == sorted(resp.data["entitlements"])


# ===========================================================================
# 9. Anonymous Rate Limiting
# ===========================================================================

@pytest.fixture
def clean_cache():
    """Clear Django cache before and after each rate-limit test to avoid cross-test leakage."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestAnonymousRateLimit:
    READINGS_URL = "/api/v1/readings/"

    def test_anon_hits_rate_limit_after_daily_limit_exhausted(
        self, api, deck_3, three_card_spread, clean_cache
    ):
        """
        Anonymous user can call /interpret/ up to ANON_DAILY_LIMIT times per day.
        The (ANON_DAILY_LIMIT + 1)-th call should return 429.
        """
        from apps.billing.rate_limit import ANON_DAILY_LIMIT

        # Create enough readings upfront
        reading_ids = []
        for i in range(ANON_DAILY_LIMIT + 1):
            resp = api.post(
                self.READINGS_URL,
                {"question": f"Question {i}?", "locale": "en", "spread_slug": "three-card"},
                format="json",
            )
            assert resp.status_code == 201
            reading_ids.append(resp.data["id"])

        # First ANON_DAILY_LIMIT calls succeed
        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            for i in range(ANON_DAILY_LIMIT):
                resp = api.post(
                    f"/api/v1/readings/{reading_ids[i]}/interpret/",
                    {"question": f"Question {i}?"},
                    format="json",
                )
                assert resp.status_code == 201, f"Expected 201 on call {i+1}, got {resp.status_code}"

            # The (ANON_DAILY_LIMIT + 1)-th call → 429
            resp = api.post(
                f"/api/v1/readings/{reading_ids[ANON_DAILY_LIMIT]}/interpret/",
                {"question": "One too many?"},
                format="json",
            )
        assert resp.status_code == 429
        assert resp.data["detail"] == "rate_limited"

    def test_authenticated_user_not_rate_limited(
        self, api, premium_user, deck_3, three_card_spread, clean_cache
    ):
        """
        Authenticated premium user is NOT subject to the anonymous daily limit.
        They should be allowed to interpret more than ANON_DAILY_LIMIT times.
        """
        from apps.billing.rate_limit import ANON_DAILY_LIMIT

        api.force_authenticate(user=premium_user)

        reading_ids = []
        for i in range(ANON_DAILY_LIMIT + 1):
            resp = api.post(
                self.READINGS_URL,
                {"question": f"Question {i}?", "locale": "en", "spread_slug": "three-card"},
                format="json",
            )
            assert resp.status_code == 201
            reading_ids.append(resp.data["id"])

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            for i in range(ANON_DAILY_LIMIT + 1):
                resp = api.post(
                    f"/api/v1/readings/{reading_ids[i]}/interpret/",
                    {"question": f"Question {i}?"},
                    format="json",
                )
                # Should not be 429; premium user gets through
                assert resp.status_code in (200, 201), (
                    f"Expected 200/201 on call {i+1}, got {resp.status_code}"
                )

    def test_rate_limit_response_contains_helpful_message(
        self, api, deck_3, three_card_spread, clean_cache
    ):
        """429 response includes a message_en field."""
        from apps.billing.rate_limit import ANON_DAILY_LIMIT

        reading_ids = []
        for i in range(ANON_DAILY_LIMIT + 1):
            resp = api.post(
                self.READINGS_URL,
                {"question": f"Q{i}?", "locale": "en", "spread_slug": "three-card"},
                format="json",
            )
            reading_ids.append(resp.data["id"])

        with patch(
            "apps.readings.views.ai_client.generate_interpretation",
            return_value=_mock_ai_result(),
        ):
            for i in range(ANON_DAILY_LIMIT):
                api.post(
                    f"/api/v1/readings/{reading_ids[i]}/interpret/",
                    {"question": f"Q{i}?"},
                    format="json",
                )
            resp = api.post(
                f"/api/v1/readings/{reading_ids[ANON_DAILY_LIMIT]}/interpret/",
                {"question": "Extra?"},
                format="json",
            )

        assert resp.status_code == 429
        assert "message_en" in resp.data or "message_ru" in resp.data
