"""Paddle webhook: signature verification, idempotency, subscription handling."""
import hashlib
import hmac
import json
import time

import pytest
from rest_framework.test import APIClient

from apps.billing.models import (
    CreditWallet,
    Entitlement,
    PaddleEvent,
    Plan,
    Subscription,
)

WEBHOOK_PATH = '/api/v1/billing/webhooks/paddle/'
TEST_SECRET = 'whsec_test_abc'


def _sign(body: bytes, secret: str = TEST_SECRET, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    payload = f'{ts}'.encode('ascii') + b':' + body
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f'ts={ts};h1={digest}'


@pytest.fixture(autouse=True)
def _set_webhook_secret(settings):
    settings.PADDLE_WEBHOOK_SECRET = TEST_SECRET


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def premium_plan(db):
    return Plan.objects.create(
        slug='premium-monthly',
        name_ru='Premium', name_en='Premium',
        kind=Plan.KIND_SUBSCRIPTION,
        price_usd_cents=500,
        monthly_included_credits=50,
        entitlement_keys=['sonnet_ai', 'celtic_cross'],
        paddle_product_id='pro_test',
        paddle_price_id='pri_test',
    )


@pytest.fixture
def credits_plan(db):
    return Plan.objects.create(
        slug='credits-small',
        name_ru='10 кредитов', name_en='10 credits',
        kind=Plan.KIND_CREDITS,
        price_usd_cents=300,
        credits_granted=10,
        paddle_price_id='pri_credits10',
    )


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username='alice', email='alice@example.com', password='pw',
    )


@pytest.mark.django_db
class TestPaddleWebhook:
    def _post(self, client, body: dict, *, sign: bool = True, ts: int | None = None):
        raw = json.dumps(body).encode('utf-8')
        headers = {}
        if sign:
            headers['HTTP_PADDLE_SIGNATURE'] = _sign(raw, ts=ts)
        return client.post(WEBHOOK_PATH, raw, content_type='application/json', **headers)

    def test_rejects_bad_signature(self, client, premium_plan, user):
        body = {'event_id': 'evt_1', 'event_type': 'subscription.activated', 'data': {}}
        raw = json.dumps(body).encode('utf-8')
        res = client.post(
            WEBHOOK_PATH, raw,
            content_type='application/json',
            HTTP_PADDLE_SIGNATURE='ts=1;h1=bogus',
        )
        assert res.status_code == 401

    def test_subscription_activated_creates_entitlements_and_credits(
        self, client, premium_plan, user,
    ):
        body = {
            'event_id': 'evt_activated_1',
            'event_type': 'subscription.activated',
            'data': {
                'id': 'sub_xyz',
                'customer_id': 'ctm_abc',
                'custom_data': {
                    'user_id': str(user.id),
                    'plan_slug': premium_plan.slug,
                },
            },
        }
        res = self._post(client, body)
        assert res.status_code == 200, res.content

        sub = Subscription.objects.get(paddle_subscription_id='sub_xyz')
        assert sub.user == user
        assert sub.status == Subscription.STATUS_ACTIVE

        ents = set(Entitlement.objects.filter(user=user).values_list('key', flat=True))
        assert ents == {'sonnet_ai', 'celtic_cross'}

        wallet = CreditWallet.objects.get(user=user)
        assert wallet.balance == 50  # monthly_included_credits

    def test_idempotency_second_delivery_is_noop(self, client, premium_plan, user):
        body = {
            'event_id': 'evt_idemp_1',
            'event_type': 'subscription.activated',
            'data': {
                'id': 'sub_idemp',
                'customer_id': 'ctm_abc',
                'custom_data': {
                    'user_id': str(user.id),
                    'plan_slug': premium_plan.slug,
                },
            },
        }
        self._post(client, body)
        self._post(client, body)

        # PaddleEvent recorded once; wallet credited once.
        assert PaddleEvent.objects.filter(event_id='evt_idemp_1').count() == 1
        assert CreditWallet.objects.get(user=user).balance == 50

    def test_subscription_canceled_marks_status(self, client, premium_plan, user):
        # Set up active sub first
        Subscription.objects.create(
            user=user, plan=premium_plan,
            paddle_subscription_id='sub_cancel',
            status=Subscription.STATUS_ACTIVE,
        )
        body = {
            'event_id': 'evt_cancel_1',
            'event_type': 'subscription.canceled',
            'data': {
                'id': 'sub_cancel',
                'custom_data': {
                    'user_id': str(user.id),
                    'plan_slug': premium_plan.slug,
                },
            },
        }
        res = self._post(client, body)
        assert res.status_code == 200

        sub = Subscription.objects.get(paddle_subscription_id='sub_cancel')
        assert sub.status == Subscription.STATUS_CANCELED
        assert sub.canceled_at is not None

    def test_credit_pack_transaction_grants_credits(self, client, credits_plan, user):
        body = {
            'event_id': 'evt_pack_1',
            'event_type': 'transaction.completed',
            'data': {
                'id': 'txn_1',
                'subscription_id': None,
                'custom_data': {
                    'user_id': str(user.id),
                    'plan_slug': credits_plan.slug,
                },
            },
        }
        res = self._post(client, body)
        assert res.status_code == 200
        assert CreditWallet.objects.get(user=user).balance == 10
