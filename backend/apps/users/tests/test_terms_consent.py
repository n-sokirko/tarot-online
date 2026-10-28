"""Accepting the Terms at registration is recorded, and never required of old clients."""
import pytest
from rest_framework.test import APIClient

from apps.users.models import User

pytestmark = pytest.mark.django_db
URL = '/api/v1/auth/register/'
PAYLOAD = {'email': 'a@example.com', 'password': 'StrongPass123!', 'display_name': 'A'}


@pytest.fixture
def api():
    return APIClient()


def test_acceptance_is_recorded_with_the_wording_it_was_given_to(api):
    resp = api.post(URL, {**PAYLOAD, 'accepted_terms': True, 'terms_version': '2026-10-28'},
                    format='json')
    assert resp.status_code == 201
    user = User.objects.get(email='a@example.com')
    assert user.terms_accepted_at is not None
    assert user.terms_version == '2026-10-28'


def test_an_older_client_that_sends_nothing_still_registers(api):
    """Existing API: the new fields are optional, so nothing breaks."""
    resp = api.post(URL, PAYLOAD, format='json')
    assert resp.status_code == 201
    user = User.objects.get(email='a@example.com')
    assert user.terms_accepted_at is None and user.terms_version == ''


def test_a_version_without_acceptance_records_nothing(api):
    api.post(URL, {**PAYLOAD, 'accepted_terms': False, 'terms_version': '2026-10-28'}, format='json')
    user = User.objects.get(email='a@example.com')
    assert user.terms_accepted_at is None and user.terms_version == ''


def test_the_acceptance_fields_are_not_echoed_back(api):
    resp = api.post(URL, {**PAYLOAD, 'accepted_terms': True, 'terms_version': 'v1'}, format='json')
    assert 'accepted_terms' not in resp.json()['user']
    assert 'terms_version' not in resp.json()['user']


def test_an_overlong_version_is_rejected_not_truncated(api):
    resp = api.post(URL, {**PAYLOAD, 'accepted_terms': True, 'terms_version': 'x' * 40}, format='json')
    assert resp.status_code == 400


class TestGoogleSignInConsent:
    URL = '/api/v1/auth/google/'
    IDINFO = {'email': 'g@example.com', 'name': 'G'}

    def _post(self, api, **extra):
        from unittest.mock import patch
        with patch('apps.users.views.id_token.verify_oauth2_token', return_value=self.IDINFO), \
             patch('apps.users.views.settings.GOOGLE_CLIENT_ID', 'cid'):
            return api.post(self.URL, {'credential': 'x', **extra}, format='json')

    def test_acceptance_sent_with_google_sign_in_is_recorded(self, api):
        assert self._post(api, accepted_terms=True, terms_version='2026-10-28').status_code == 200
        user = User.objects.get(email='g@example.com')
        assert user.terms_accepted_at is not None and user.terms_version == '2026-10-28'

    def test_signing_in_again_does_not_overwrite_the_first_acceptance(self, api):
        self._post(api, accepted_terms=True, terms_version='old')
        first = User.objects.get(email='g@example.com').terms_accepted_at
        self._post(api, accepted_terms=True, terms_version='new')
        user = User.objects.get(email='g@example.com')
        assert user.terms_accepted_at == first and user.terms_version == 'old'

    def test_no_acceptance_sent_records_nothing(self, api):
        self._post(api)
        assert User.objects.get(email='g@example.com').terms_accepted_at is None
