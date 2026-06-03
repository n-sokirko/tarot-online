"""
Send the daily "card of the day" push to subscribed Telegram users.

Each subscriber gets a card chosen deterministically from (today | their tg_id),
so everyone gets a stable, personal card for the day. Run daily (Celery beat or
cron):  python manage.py send_daily_push
"""
import datetime
import hashlib

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send the daily card-of-the-day push to subscribed Telegram users."

    def handle(self, *args, **options) -> None:
        import requests
        from apps.tarot.models import Card
        from apps.telegram_bot.models import TelegramUser

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stderr.write("TELEGRAM_BOT_TOKEN not set.")
            return

        cards = list(Card.objects.all())
        if not cards:
            self.stderr.write("No cards seeded.")
            return

        webapp = getattr(settings, "WEBAPP_URL", "https://sokirdon.com")
        today = datetime.date.today().isoformat()
        subs = list(TelegramUser.objects.filter(daily_push=True))
        sent = 0

        for u in subs:
            seed = hashlib.sha256(f"{today}|{u.tg_id}".encode()).digest()
            card = cards[seed[0] % len(cards)]
            is_reversed = bool(seed[1] & 1)
            kws = (card.keywords_ru or [])[:3]
            rev = " (перевёрнута)" if is_reversed else ""
            text = (
                f"🌙 *Карта дня*\n\n"
                f"*{card.name_ru}*{rev}\n"
                f"{' · '.join(kws)}\n\n"
                f"Полный расклад — {webapp}"
            )
            try:
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": u.tg_id, "text": text, "parse_mode": "Markdown"},
                    timeout=15,
                )
                if r.ok and r.json().get("ok"):
                    sent += 1
            except Exception:  # noqa: BLE001 — best-effort; skip failures (blocked bot etc.)
                continue

        self.stdout.write(self.style.SUCCESS(f"Daily push sent to {sent}/{len(subs)} subscribers."))
