"""
Send the daily "card of the day" push to all Telegram users.

Each user gets a card chosen deterministically from (today | their tg_id),
so everyone gets a stable, personal card for the day. Run daily (Celery beat or
cron):  python manage.py send_daily_push
"""
import datetime
import hashlib

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send the daily card-of-the-day push to all Telegram users."

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
        users = list(TelegramUser.objects.all())
        sent = 0
        failed = 0

        for u in users:
            seed = hashlib.sha256(f"{today}|{u.tg_id}".encode()).digest()
            card = cards[seed[0] % len(cards)]
            is_reversed = bool(seed[1] & 1)
            is_ru = (getattr(u, "locale", "ru") or "ru").startswith("ru")

            if is_ru:
                kws = (card.keywords_ru or [])[:3]
                rev = " (перевёрнута)" if is_reversed else ""
                text = (
                    f"🌙 *Карта дня*\n\n"
                    f"*{card.name_ru}*{rev}\n"
                    f"_{' · '.join(kws)}_\n\n"
                    f"Что она значит именно для тебя сегодня?\n"
                    f"Сделай расклад 👇"
                )
                btn = "🔮 Открыть расклад"
            else:
                kws = (card.keywords_en or [])[:3]
                rev = " (reversed)" if is_reversed else ""
                text = (
                    f"🌙 *Card of the Day*\n\n"
                    f"*{card.name_en}*{rev}\n"
                    f"_{' · '.join(kws)}_\n\n"
                    f"What does it mean for you today?\n"
                    f"Draw your spread 👇"
                )
                btn = "🔮 Open a reading"

            reply_markup = {
                "inline_keyboard": [[
                    {"text": btn, "web_app": {"url": webapp}}
                ]]
            }
            try:
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": u.tg_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "reply_markup": reply_markup,
                    },
                    timeout=15,
                )
                if r.ok and r.json().get("ok"):
                    sent += 1
                else:
                    failed += 1
            except Exception:  # noqa: BLE001 — best-effort; skip failures (blocked bot etc.)
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Daily push sent to {sent}/{len(users)} users ({failed} failed)."
        ))
