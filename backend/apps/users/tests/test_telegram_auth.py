"""
Tests for Telegram Mini App authentication endpoint.

POST /api/v1/auth/telegram-webapp/
- Validates HMAC-SHA256 initData signature per Telegram spec
- Creates user + TelegramUser profile on first login
- Returns JWT tokens
"""
import hashlib
import hmac
import json
import time
import urllib.parse

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.telegram_bot.models import TelegramUser

User = get_user_model()

BOT_TOKEN = 'test_bot_token_1234567890:AAABBBCCC'


def _make_init_data(tg_user_dict: dict, bot_token: str = BOT_TOKEN) -> str:
    """Build a valid Telegram initData string (signs with the given token)."""
    user_json = json.dumps(tg_user_dict, separators=(',', ':'))
    auth_date = int(time.time())

    params = {
        'auth_date': str(auth_date),
        'user': user_json,
    }
    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(params.items()))

    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    params['hash'] = hash_value
    return urllib.parse.urlencode(params)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def settings_with_bot_token(settings):
    settings.TELEGRAM_BOT_TOKEN = BOT_TOKEN
    return settings


@pytest.mark.django_db
class TestTelegramWebAppAuth:
    URL = '/api/v1/auth/telegram-webapp/'

    def test_missing_init_data_returns_400(self, api, settings_with_bot_token):
        resp = api.post(self.URL, {}, format='json')
        assert resp.status_code == 400
        assert 'error' in resp.data

    def test_invalid_signature_returns_400(self, api, settings_with_bot_token):
        # Tampered initData (wrong bot token used to sign)
        init_data = _make_init_data({'id': 123, 'first_name': 'Alice'}, bot_token='wrong_token')
        resp = api.post(self.URL, {'init_data': init_data}, format='json')
        assert resp.status_code == 400
        assert resp.data['error'] == 'Invalid initData signature.'

    def test_valid_initdata_creates_user_and_returns_tokens(self, api, settings_with_bot_token):
        tg_user = {'id': 42, 'first_name': 'Alice', 'username': 'alice_tg'}
        init_data = _make_init_data(tg_user)

        resp = api.post(self.URL, {'init_data': init_data}, format='json')

        assert resp.status_code == 200
        assert 'access' in resp.data
        assert 'refresh' in resp.data
        assert 'user' in resp.data

        # A TelegramUser profile is created
        profile = TelegramUser.objects.get(tg_id=42)
        assert profile.tg_username == 'alice_tg'
        assert profile.tg_first_name == 'Alice'

        # A Django user is created with a telegram-local email
        assert profile.user is not None
        assert profile.user.email == 'tg_42@telegram.local'

    def test_second_login_same_user_no_duplicate(self, api, settings_with_bot_token):
        tg_user = {'id': 99, 'first_name': 'Bob'}
        init_data = _make_init_data(tg_user)

        api.post(self.URL, {'init_data': init_data}, format='json')
        api.post(self.URL, {'init_data': init_data}, format='json')

        # Should not create duplicate users or profiles
        assert TelegramUser.objects.filter(tg_id=99).count() == 1
        assert User.objects.filter(email='tg_99@telegram.local').count() == 1

    def test_telegram_not_configured_returns_503(self, api, settings):
        settings.TELEGRAM_BOT_TOKEN = ''
        resp = api.post(self.URL, {'init_data': 'anything'}, format='json')
        assert resp.status_code == 503

    def test_profile_fields_updated_on_subsequent_login(self, api, settings_with_bot_token):
        """Second login with different username/name should update the profile."""
        tg_user = {'id': 77, 'first_name': 'Carl', 'username': 'carl_old'}
        init_data = _make_init_data(tg_user)
        api.post(self.URL, {'init_data': init_data}, format='json')

        tg_user2 = {'id': 77, 'first_name': 'Carl Updated', 'username': 'carl_new'}
        init_data2 = _make_init_data(tg_user2)
        api.post(self.URL, {'init_data': init_data2}, format='json')

        profile = TelegramUser.objects.get(tg_id=77)
        assert profile.tg_username == 'carl_new'
        assert profile.tg_first_name == 'Carl Updated'
