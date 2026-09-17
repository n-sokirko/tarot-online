"""
Management command: set_telegram_webhook

Registers this deployment's public URL with Telegram as the bot's webhook,
replacing long-polling. Idempotent — safe to call on every deploy (see
start-railway-web.sh): if nothing changed, Telegram just confirms the same
registration.

Usage: python manage.py set_telegram_webhook [--drop-pending]
"""
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Register this deployment's public URL as the Telegram bot webhook."

    def add_arguments(self, parser):
        parser.add_argument(
            '--drop-pending',
            action='store_true',
            help='Discard updates Telegram queued while the webhook was unreachable. '
                 'Off by default so a redeploy does not swallow real user messages.',
        )

    def handle(self, *args, **options) -> None:
        import httpx

        from apps.telegram_bot.bot import BOT_ALLOWED_UPDATES

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stdout.write(self.style.WARNING('TELEGRAM_BOT_TOKEN is not set — skipping.'))
            return

        base_url = settings.TELEGRAM_WEBHOOK_BASE_URL.rstrip('/')
        if not base_url:
            self.stdout.write(self.style.WARNING('TELEGRAM_WEBHOOK_BASE_URL is not set — skipping.'))
            return

        webhook_url = f'{base_url}/api/v1/telegram/webhook/'
        payload = {
            # chat_member is off by default and must be requested explicitly,
            # otherwise the contest invite tally never fires — same list the
            # polling loop used.
            'allowed_updates': list(BOT_ALLOWED_UPDATES),
            'url': webhook_url,
        }
        if options['drop_pending']:
            payload['drop_pending_updates'] = True
        if settings.TELEGRAM_WEBHOOK_SECRET:
            payload['secret_token'] = settings.TELEGRAM_WEBHOOK_SECRET
        else:
            # Without a secret the view refuses every update, so registering the
            # URL would give a bot that silently answers nothing.
            self.stderr.write(self.style.ERROR(
                'TELEGRAM_WEBHOOK_SECRET is not set — the webhook view will reject every '
                'update (fail closed). Set it before registering the webhook.'
            ))
            return

        try:
            resp = httpx.post(
                f'https://api.telegram.org/bot{token}/setWebhook', json=payload, timeout=15,
            )
            data = resp.json()
        except httpx.HTTPError as exc:
            self.stderr.write(self.style.ERROR(f'Could not reach Telegram API: {exc}'))
            return

        if not data.get('ok'):
            self.stderr.write(self.style.ERROR(f'Telegram rejected the webhook: {data}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Webhook set to {webhook_url} (setWebhook ok=True)'))

        # ok=True only means Telegram accepted the call — it does not confirm
        # what Telegram actually has on file. Ask it to echo its own record so
        # the deploy log answers "did the webhook really register?" definitively.
        try:
            info = httpx.get(
                f'https://api.telegram.org/bot{token}/getWebhookInfo', timeout=15,
            ).json().get('result', {})
        except httpx.HTTPError as exc:
            self.stderr.write(self.style.WARNING(
                f'setWebhook succeeded but could not verify via getWebhookInfo: {exc}'
            ))
            return

        registered_url = info.get('url', '')
        if registered_url == webhook_url:
            self.stdout.write(self.style.SUCCESS(
                f'Confirmed via getWebhookInfo: Telegram has {registered_url} on file '
                f'(pending_update_count={info.get("pending_update_count", 0)}).'
            ))
        else:
            self.stderr.write(self.style.ERROR(
                f'getWebhookInfo mismatch: Telegram has url={registered_url!r}, '
                f'expected {webhook_url!r}. Webhook is NOT correctly registered.'
            ))

        last_error = info.get('last_error_message')
        if last_error:
            self.stderr.write(self.style.WARNING(
                f"Telegram last_error_message: {last_error} "
                f"(last_error_date={info.get('last_error_date')}) — Telegram's own record of "
                f'the most recent delivery failure, e.g. a 403 from our webhook.'
            ))
