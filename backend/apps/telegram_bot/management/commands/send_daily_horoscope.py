"""
Send the daily personal horoscope push to subscribed users who have a birth date.

For each TelegramUser with daily_push=True we resolve their birth date (stored
field, else their most recent natal chart), derive the zodiac sign, and send a
short personal horoscope with a button into the Mini App. Users without a known
birth date are skipped (they still get the card-of-the-day push).

  python manage.py send_daily_horoscope            # all subscribers
  python manage.py send_daily_horoscope --tg-id 42 # just one user (testing)
  python manage.py send_daily_horoscope --all      # everyone, ignore daily_push
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send the daily personal horoscope push to subscribed users with a birth date."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--tg-id", type=int, default=None,
                            help="Send only to this Telegram id (for testing).")
        parser.add_argument("--username", type=str, default=None,
                            help="Send only to this @username (without the @).")
        parser.add_argument("--all", action="store_true",
                            help="Send to every user, not only daily_push subscribers.")

    def handle(self, *args, **options) -> None:
        from apps.telegram_bot.models import TelegramUser
        from apps.telegram_bot.push import send_horoscope_push

        qs = TelegramUser.objects.select_related("user")
        if options["tg_id"]:
            qs = qs.filter(tg_id=options["tg_id"])
        elif options["username"]:
            qs = qs.filter(tg_username__iexact=options["username"].lstrip("@"))
        elif not options["all"]:
            qs = qs.filter(daily_push=True)

        result = send_horoscope_push(qs)
        if result.get("error"):
            self.stderr.write(result["error"])
            return
        self.stdout.write(self.style.SUCCESS(
            f"Daily horoscope: sent {result['sent']}, "
            f"skipped {result['skipped']} (no birth date), {result['failed']} failed."
        ))
