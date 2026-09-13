"""
Send the daily "card of the day" push to Telegram users.

Each user gets a card chosen deterministically from (today | their tg_id),
so everyone gets a stable, personal card for the day. Run daily (Celery beat or
cron):  python manage.py send_daily_push

  python manage.py send_daily_push             # everyone
  python manage.py send_daily_push --tg-id 42  # just one user (testing)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send the daily card-of-the-day push to all Telegram users."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--tg-id", type=int, default=None,
                            help="Send only to this Telegram id (for testing).")

    def handle(self, *args, **options) -> None:
        from apps.telegram_bot.models import TelegramUser
        from apps.telegram_bot.push import send_card_push

        qs = TelegramUser.objects.all()
        if options["tg_id"]:
            qs = qs.filter(tg_id=options["tg_id"])

        result = send_card_push(qs)
        if result.get("error"):
            self.stderr.write(result["error"])
            return
        self.stdout.write(self.style.SUCCESS(
            f"Daily push sent to {result['sent']} users ({result['failed']} failed)."
        ))
