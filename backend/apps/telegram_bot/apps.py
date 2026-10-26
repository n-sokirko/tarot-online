from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.telegram_bot'
    verbose_name = 'Telegram Bot'

    def ready(self) -> None:
        from apps.telegram_bot import signals  # noqa: F401 — registers the receivers
