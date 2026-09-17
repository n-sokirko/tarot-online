"""HTTP entry point for Telegram updates (webhook mode)."""
import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class TelegramWebhookView(APIView):
    """
    POST /api/v1/telegram/webhook/

    Telegram pushes updates here instead of us long-polling for them, so the
    bot lives inside the already-running web service and needs no separate
    always-on process. The URL is registered with Telegram by
    `manage.py set_telegram_webhook` (run on every deploy, see
    start-railway-web.sh).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(exclude=True)
    def post(self, request):
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        if not secret:
            # Fail closed: with no secret configured there is no way to tell a
            # genuine Telegram update from anyone else POSTing to this public
            # URL — better to accept nothing than to accept unauthenticated
            # updates. Set TELEGRAM_WEBHOOK_SECRET (see .env.example) to enable
            # delivery. 403 rather than 5xx: this is an expected configuration
            # state, not a server fault.
            logger.error(
                'Telegram webhook called but TELEGRAM_WEBHOOK_SECRET is not configured — '
                'refusing the request (fail closed).'
            )
            return Response(status=status.HTTP_403_FORBIDDEN)

        received = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if received != secret:
            # A secret IS configured, so this is a different failure mode from
            # the branch above — a forged request, a proxy stripping the header,
            # or (most likely while setting things up) the value on Railway not
            # matching the one the webhook was registered with. Log it without
            # echoing either secret so it is distinguishable in deploy logs.
            logger.warning(
                'Telegram webhook secret mismatch — refusing the request. '
                'header_present=%s header_len=%s expected_len=%s',
                received is not None, len(received or ''), len(secret),
            )
            return Response(status=status.HTTP_403_FORBIDDEN)

        from apps.telegram_bot.bot_runtime import process_update_sync

        try:
            process_update_sync(request.data)
        except Exception:
            # Answer 200 no matter what: Telegram retries an update with a
            # growing backoff when it does not get a prompt success, and on
            # repeated failures it can suspend delivery altogether. The cost is
            # that a broken handler is invisible outside the logs — watch the
            # Railway log for this line.
            logger.exception('Failed to process Telegram webhook update')
        return Response({'ok': True})
