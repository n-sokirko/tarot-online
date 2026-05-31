"""
Refund a Telegram Stars payment — useful for safely testing real payments.

Telegram Stars have no separate "test card": you pay with real Stars and then
refund them back to yourself. This calls the Bot API `refundStarPayment` method.

You need the payer's Telegram user id and the telegram_payment_charge_id — both
are printed to the bot logs on every successful payment:
    STARS PAYMENT ok: payer_tg_id=... charge_id=... amount=...

Usage:
    python manage.py refund_star_payment <payer_tg_id> <charge_id>
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Refund a Telegram Stars payment by payer id + charge id."

    def add_arguments(self, parser):
        parser.add_argument("payer_tg_id", type=int, help="Telegram user id of the payer")
        parser.add_argument("charge_id", type=str, help="telegram_payment_charge_id")

    def handle(self, *args, **options):
        import requests

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not configured.")

        payer_tg_id = options["payer_tg_id"]
        charge_id = options["charge_id"]

        url = f"https://api.telegram.org/bot{token}/refundStarPayment"
        try:
            resp = requests.post(
                url,
                json={"user_id": payer_tg_id, "telegram_payment_charge_id": charge_id},
                timeout=15,
            )
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"Request failed: {exc}")

        if data.get("ok"):
            self.stdout.write(self.style.SUCCESS(
                f"✓ Refunded charge {charge_id} to user {payer_tg_id}. "
                f"Stars returned to the payer."
            ))
        else:
            raise CommandError(f"Telegram API error: {data}")
