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


class Broadcast(models.Model):
    """A message broadcast to Telegram users, sent from the admin panel."""
    TARGET_ALL = 'all'
    TARGET_SUBSCRIBERS = 'subscribers'
    TARGET_CHOICES = [
        (TARGET_ALL, 'Все пользователи бота'),
        (TARGET_SUBSCRIBERS, 'Только подписчики (/subscribe)'),
    ]

    title = models.CharField(max_length=120, blank=True, help_text='Только для тебя, в сообщение не идёт.')
    message = models.TextField(help_text='Текст рассылки. Поддерживает Markdown.')
    target = models.CharField(max_length=16, choices=TARGET_CHOICES, default=TARGET_ALL)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        status = 'отправлена' if self.sent_at else 'черновик'
        return f'{self.title or self.message[:40]} — {status}'

