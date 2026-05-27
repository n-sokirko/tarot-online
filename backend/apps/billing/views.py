"""Billing endpoints. Paddle is the merchant of record."""
from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing import services as billing_services
from apps.billing.models import PaddleEvent, Plan, Subscription
from apps.billing.paddle import verify_signature
from apps.billing.serializers import (
    BillingMeSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)

User = get_user_model()
log = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def plans_list(_request: Request) -> Response:
    plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'price_usd_cents')
    return Response({
        'plans': PlanSerializer(plans, many=True).data,
        'telegram_bot_username': settings.TELEGRAM_BOT_USERNAME,
        'paddle_client_token': settings.PADDLE_CLIENT_TOKEN,
        'paddle_env': settings.PADDLE_ENV,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def billing_me(request: Request) -> Response:
    user = request.user
    info = billing_services.tier_for(user)
    sub = (
        Subscription.objects.filter(
            user=user,
            status__in=[Subscription.STATUS_ACTIVE, Subscription.STATUS_TRIALING],
        )
        .select_related('plan')
        .order_by('-created_at')
        .first()
    )
    payload = {
        'tier': info.tier,
        'credits': billing_services.credits_balance(user),
        'entitlements': sorted(info.entitlements),
        'subscription': SubscriptionSerializer(sub).data if sub else None,
    }
    return Response(BillingMeSerializer(payload).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request: Request) -> Response:
    """Returns the inputs the frontend hands to Paddle.js inline checkout.

    Frontend calls Paddle.Checkout.open() with this payload. We do not redirect
    server-side: keeping the user on our domain gives a smoother UX.
    """
    slug = request.data.get('plan_slug')
    if not slug:
        return Response({'detail': 'plan_slug is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        plan = Plan.objects.get(slug=slug, is_active=True)
    except Plan.DoesNotExist:
        return Response({'detail': 'plan not found'}, status=status.HTTP_404_NOT_FOUND)
    if plan.kind == Plan.KIND_FREE:
        return Response({'detail': 'free plan does not require checkout'},
                        status=status.HTTP_400_BAD_REQUEST)
    if not plan.paddle_price_id:
        return Response({
            'detail': 'plan_not_configured',
            'message': 'This plan has no Paddle price configured yet. Set PADDLE_PRICE_* in env.',
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'paddle_client_token': settings.PADDLE_CLIENT_TOKEN,
        'paddle_env': settings.PADDLE_ENV,
        'price_id': plan.paddle_price_id,
        'plan_slug': plan.slug,
        'customer_email': request.user.email,
        'custom_data': {
            'user_id': str(request.user.id),
            'plan_slug': plan.slug,
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def telegram_checkout(request: Request) -> Response:
    """Generate a Telegram deep-link for Stars payment."""
    slug = request.data.get('plan_slug')
    if not slug:
        return Response({'detail': 'plan_slug is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        plan = Plan.objects.get(slug=slug, is_active=True)
    except Plan.DoesNotExist:
        return Response({'detail': 'plan not found'}, status=status.HTTP_404_NOT_FOUND)
    if plan.kind == Plan.KIND_FREE:
        return Response({'detail': 'free plan does not require checkout'},
                        status=status.HTTP_400_BAD_REQUEST)
    if not plan.tg_stars_price:
        return Response({'detail': 'plan_not_configured',
                         'message': 'Set tg_stars_price in admin or via seed_plans.'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    from apps.telegram_bot.tokens import generate_payment_token
    token = generate_payment_token(request.user.id, plan.slug)
    return Response({
        'url': f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=buy_{token}",
        'stars': plan.tg_stars_price,
        'plan': PlanSerializer(plan).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def telegram_invoice(request: Request) -> Response:
    """
    Create a Telegram invoice link for use with WebApp.openInvoice().

    This is the Mini App payment path: instead of redirecting the user to the bot
    via a deep-link, we create an invoice link server-side and let the Telegram
    WebApp SDK show the native Stars payment sheet inline.
    """
    import requests as http_requests

    slug = request.data.get('plan_slug')
    if not slug:
        return Response({'detail': 'plan_slug is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        plan = Plan.objects.get(slug=slug, is_active=True)
    except Plan.DoesNotExist:
        return Response({'detail': 'plan not found'}, status=status.HTTP_404_NOT_FOUND)
    if plan.kind == Plan.KIND_FREE:
        return Response({'detail': 'free plan does not require checkout'},
                        status=status.HTTP_400_BAD_REQUEST)
    if not plan.tg_stars_price:
        return Response({'detail': 'plan_not_configured'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if not settings.TELEGRAM_BOT_TOKEN:
        return Response({'detail': 'telegram_not_configured'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    tg_url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/createInvoiceLink'
    try:
        resp = http_requests.post(tg_url, json={
            'title': plan.name_ru,
            'description': plan.description_ru[:255],
            'payload': f'buy|{plan.slug}|{request.user.id}',
            'currency': 'XTR',
            'prices': [{'label': plan.name_ru, 'amount': plan.tg_stars_price}],
            'provider_token': '',
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.error('createInvoiceLink failed: %s', exc)
        return Response({'detail': 'telegram_api_error'}, status=status.HTTP_502_BAD_GATEWAY)

    if not data.get('ok'):
        log.error('createInvoiceLink error response: %s', data)
        return Response({'detail': 'telegram_api_error'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({
        'invoice_link': data['result'],
        'stars': plan.tg_stars_price,
        'plan': PlanSerializer(plan).data,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def paddle_webhook(request: Request) -> Response:
    raw = request.body
    sig = request.headers.get('Paddle-Signature', '')
    secret = settings.PADDLE_WEBHOOK_SECRET

    if secret and not verify_signature(raw_body=raw, signature_header=sig, secret=secret):
        log.warning('paddle webhook: bad signature')
        return Response({'detail': 'bad signature'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = json.loads(raw or b'{}')
    except json.JSONDecodeError:
        return Response({'detail': 'invalid json'}, status=status.HTTP_400_BAD_REQUEST)

    event_id = payload.get('event_id') or payload.get('notification_id') or ''
    event_type = payload.get('event_type') or ''
    if not event_id:
        return Response({'detail': 'missing event_id'}, status=status.HTTP_400_BAD_REQUEST)

    # Idempotency
    record, created = PaddleEvent.objects.get_or_create(
        event_id=event_id,
        defaults={'event_type': event_type, 'payload': payload},
    )
    if not created:
        return Response({'ok': True, 'idempotent': True})

    try:
        _handle_event(event_type, payload)
        from django.utils import timezone
        record.processed_at = timezone.now()
        record.save(update_fields=['processed_at'])
    except Exception as exc:  # noqa: BLE001 — webhook handler should not 500
        log.exception('paddle webhook %s failed', event_type)
        record.error = repr(exc)[:2000]
        record.save(update_fields=['error'])
        return Response({'ok': False, 'detail': 'handler error'}, status=500)

    return Response({'ok': True})


def _handle_event(event_type: str, payload: dict) -> None:
    data = payload.get('data') or {}
    custom = (data.get('custom_data') or {}) if isinstance(data, dict) else {}
    user_id = custom.get('user_id') if isinstance(custom, dict) else None
    plan_slug = custom.get('plan_slug') if isinstance(custom, dict) else None

    if not user_id or not plan_slug:
        log.warning('paddle webhook %s: missing custom_data %s', event_type, custom)
        return

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        log.warning('paddle webhook %s: user %s not found', event_type, user_id)
        return

    try:
        plan = Plan.objects.get(slug=plan_slug)
    except Plan.DoesNotExist:
        log.warning('paddle webhook %s: plan %s not found', event_type, plan_slug)
        return

    if event_type in ('subscription.created', 'subscription.activated', 'subscription.updated'):
        period_start = parse_datetime(data.get('current_billing_period', {}).get('starts_at', '') or '')
        period_end = parse_datetime(data.get('current_billing_period', {}).get('ends_at', '') or '')
        billing_services.apply_subscription_activated(
            user=user,
            plan=plan,
            paddle_subscription_id=data.get('id', ''),
            paddle_customer_id=data.get('customer_id', '') or '',
            period_start=period_start,
            period_end=period_end,
        )
    elif event_type in ('subscription.canceled', 'subscription.cancelled'):
        billing_services.apply_subscription_canceled(
            paddle_subscription_id=data.get('id', '')
        )
    elif event_type == 'transaction.completed':
        # Either a subscription renewal (subscription_id present) or a one-time pack.
        sub_id = data.get('subscription_id')
        if sub_id:
            # Renewal: re-apply (idempotent) to refresh entitlements + monthly credits.
            billing_services.apply_subscription_activated(
                user=user,
                plan=plan,
                paddle_subscription_id=sub_id,
                paddle_customer_id=data.get('customer_id', '') or '',
            )
        elif plan.kind == Plan.KIND_CREDITS:
            billing_services.apply_pack_purchase(
                user=user, plan=plan,
                reference_id=data.get('id', ''),
            )
