"""Management command: run the Telegram bot in polling mode (development only)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run @tarott_online_bot in polling mode (dev). Use webhook in production.'

    def handle(self, *args, **options) -> None:
        from apps.telegram_bot.bot import create_application

        app = create_application()
        self.stdout.write(self.style.SUCCESS('Bot polling started (@tarott_online_bot). Ctrl-C to stop.'))
        app.run_polling(drop_pending_updates=True)
