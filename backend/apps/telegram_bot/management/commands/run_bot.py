"""Management command: run the Telegram bot in polling mode (development only)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run @tarott_online_bot in polling mode (dev). Use webhook in production.'

    def handle(self, *args, **options) -> None:
        from apps.telegram_bot.bot import create_application, BOT_ALLOWED_UPDATES

        app = create_application()
        self.stdout.write(self.style.SUCCESS('Bot polling started (@tarott_online_bot). Ctrl-C to stop.'))
        # chat_member updates are off by default — must be in allowed_updates
        # explicitly, otherwise contest-invite tally never fires.
        app.run_polling(drop_pending_updates=True, allowed_updates=BOT_ALLOWED_UPDATES)
