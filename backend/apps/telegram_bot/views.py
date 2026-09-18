"""HTTP entry points for Telegram: the bot webhook and the channel autoposter."""
import logging
import random

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class _ChannelTokenMixin:
    """Shared bearer-style auth for the two autoposter endpoints.

    The channel autoposter is a scheduled Claude Code routine running in
    Anthropic's cloud: it has no access to this machine, the repo or the bot
    token, so it authenticates with one narrow secret that only lets it read the
    already-used topics and publish a post. Fail closed when it is unset, exactly
    like the webhook view — an unauthenticated publish endpoint would let anyone
    post into the channel.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def check_token(self, request):
        secret = getattr(settings, 'CHANNEL_POST_TOKEN', '')
        if not secret:
            logger.error('Channel endpoint called but CHANNEL_POST_TOKEN is not configured.')
            return Response({'detail': 'channel posting is not configured'},
                            status=status.HTTP_403_FORBIDDEN)
        if request.headers.get('X-Channel-Token') != secret:
            logger.warning('Channel endpoint: bad or missing X-Channel-Token.')
            return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return None


class ChannelBriefView(_ChannelTokenMixin, APIView):
    """
    GET /api/v1/channel/brief/

    Everything the autoposter needs to write the next post without repeating
    itself: which kind is due, an angle to stay inside, and the topics already
    covered. The post texts themselves are not returned — the ban list is what
    steers generation, and shipping the full history would only invite the model
    to paraphrase it.
    """
    @extend_schema(exclude=True)
    def get(self, request):
        denied = self.check_token(request)
        if denied:
            return denied

        from apps.telegram_bot import channel
        from apps.telegram_bot.models import ChannelPost

        kind = channel.next_kind()
        angle = random.choice(channel.ANGLES) if kind == ChannelPost.KIND_FACT else None
        return Response({
            'kind': kind,
            'angle': angle,
            # The editorial brief travels with the response so the routine's own
            # prompt can stay short and the voice stays editable in the repo.
            'guidelines': channel.guidelines(kind, angle),
            'used_topics': channel._ban_list(),
            'published_total': ChannelPost.objects.filter(
                status=ChannelPost.STATUS_PUBLISHED).count(),
            'similarity_limit': channel.SIMILARITY_LIMIT,
        })


class ChannelPublishView(_ChannelTokenMixin, APIView):
    """
    POST /api/v1/channel/publish/  {"topic": "...", "text": "...", "kind": "fact"}

    Checks the post against recent ones and, if it is genuinely new, sends it to
    the channel and records it. A near-duplicate comes back as 409 with the topic
    it collided with, so the caller can try a different angle instead of quietly
    publishing the same thing twice.
    """
    @extend_schema(exclude=True)
    def post(self, request):
        denied = self.check_token(request)
        if denied:
            return denied

        from apps.telegram_bot import channel
        from apps.telegram_bot.models import ChannelPost

        topic = (request.data.get('topic') or '').strip()
        text = (request.data.get('text') or '').strip()
        kind = request.data.get('kind') or channel.next_kind()
        if not topic or not text:
            return Response({'detail': 'topic and text are required'},
                            status=status.HTTP_400_BAD_REQUEST)
        if kind not in dict(ChannelPost.KIND_CHOICES):
            return Response({'detail': f'unknown kind {kind!r}'},
                            status=status.HTTP_400_BAD_REQUEST)

        worst_score, worst_topic = 0.0, ''
        for old_topic, old_text in ChannelPost.objects.order_by('-created_at').values_list(
                'topic', 'text')[:channel.SIMILARITY_WINDOW]:
            score = channel.similarity(text, old_text)
            if score > worst_score:
                worst_score, worst_topic = score, old_topic
        if worst_score >= channel.SIMILARITY_LIMIT:
            return Response(
                {'detail': 'too similar to a recent post',
                 'similarity': round(worst_score, 3),
                 'conflicts_with': worst_topic},
                status=status.HTTP_409_CONFLICT,
            )

        row = ChannelPost.objects.create(
            kind=kind, topic=topic[:200], text=text,
            fingerprint=channel.fingerprint(text),
            model_used=(request.data.get('model') or '')[:64],
            attempts=int(request.data.get('attempts') or 1),
        )
        try:
            message_id = channel.send_to_channel(text)
        except Exception as exc:  # noqa: BLE001 — recorded, then reported
            row.status = ChannelPost.STATUS_FAILED
            row.error = str(exc)[:2000]
            row.save(update_fields=['status', 'error'])
            logger.exception('Channel publish failed')
            return Response({'detail': f'send failed: {exc}'},
                            status=status.HTTP_502_BAD_GATEWAY)

        row.status = ChannelPost.STATUS_PUBLISHED
        row.published_at = timezone.now()
        row.tg_message_id = message_id
        row.save(update_fields=['status', 'published_at', 'tg_message_id'])
        return Response({'ok': True, 'message_id': message_id, 'id': row.id,
                         'similarity': round(worst_score, 3)},
                        status=status.HTTP_201_CREATED)


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
