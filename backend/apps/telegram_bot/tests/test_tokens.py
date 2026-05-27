"""
Tests for Telegram payment token generation and validation.

The token is embedded in the t.me deep-link used to redirect users
from the website to the bot for Stars payment.
"""
import time
import pytest

from apps.telegram_bot.tokens import generate_payment_token, validate_payment_token


SECRET = 'a' * 64  # 64-char hex secret for tests


@pytest.fixture(autouse=True)
def patch_secret(settings):
    settings.TELEGRAM_PAYMENT_SECRET = SECRET


class TestGenerateToken:
    def test_token_has_two_parts(self):
        token = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        parts = token.split('.')
        assert len(parts) == 2

    def test_different_users_produce_different_tokens(self):
        t1 = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        t2 = generate_payment_token(user_id=2, plan_slug='premium-monthly')
        assert t1 != t2

    def test_different_plans_produce_different_tokens(self):
        t1 = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        t2 = generate_payment_token(user_id=1, plan_slug='credits-small')
        assert t1 != t2


class TestValidateToken:
    def test_valid_token_returns_payload(self):
        token = generate_payment_token(user_id=42, plan_slug='premium-monthly')
        payload = validate_payment_token(token)
        assert payload is not None
        assert payload['user_id'] == 42
        assert payload['plan_slug'] == 'premium-monthly'

    def test_tampered_signature_returns_none(self):
        token = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        b64, sig = token.rsplit('.', 1)
        tampered = f'{b64}.{"x" * len(sig)}'
        assert validate_payment_token(tampered) is None

    def test_tampered_payload_returns_none(self):
        token = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        import base64, json
        b64, sig = token.rsplit('.', 1)
        pad = (4 - len(b64) % 4) % 4
        data = json.loads(base64.urlsafe_b64decode(b64 + '=' * pad))
        # Tamper with user_id
        data['u'] = 999
        new_b64 = base64.urlsafe_b64encode(
            json.dumps(data, separators=(',', ':')).encode()
        ).decode().rstrip('=')
        tampered = f'{new_b64}.{sig}'
        assert validate_payment_token(tampered) is None

    def test_expired_token_returns_none(self):
        token = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        # max_age=0 → immediately expired
        assert validate_payment_token(token, max_age=0) is None

    def test_garbage_string_returns_none(self):
        assert validate_payment_token('not.a.valid.token') is None
        assert validate_payment_token('') is None
        assert validate_payment_token('nodot') is None

    def test_wrong_secret_returns_none(self, settings):
        token = generate_payment_token(user_id=1, plan_slug='premium-monthly')
        settings.TELEGRAM_PAYMENT_SECRET = 'b' * 64  # different secret
        assert validate_payment_token(token) is None
