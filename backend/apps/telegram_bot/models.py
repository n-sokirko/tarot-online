from django.conf import settings
from django.db import models


class TelegramUser(models.Model):
    """Links a Telegram account to a Django user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_profile',
        null=True,
        blank=True,
    )
    tg_id = models.BigIntegerField(unique=True)
    tg_username = models.CharField(max_length=64, blank=True)
    tg_first_name = models.CharField(max_length=64, blank=True)
    # Opt-in to the daily "card of the day" push (toggled via /subscribe).
    daily_push = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __str__(self) -> str:
        return f'@{self.tg_username or self.tg_id} → user:{self.user_id}'
