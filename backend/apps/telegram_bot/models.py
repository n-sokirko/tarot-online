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
    # Telegram client language (from user.language_code), used to localise pushes.
    locale = models.CharField(max_length=8, default='ru')
    # Opt-in to the daily "card of the day" push (toggled via /subscribe).
    daily_push = models.BooleanField(default=False)
    # Birth date for the personal daily horoscope. Collected via /birthday or
    # auto-imported from the user's natal chart. Null until known.
    birth_date = models.DateField(null=True, blank=True)
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


class ChannelPost(models.Model):
    """One post written for the public channel by `manage.py post_to_channel`.

    This table is the whole anti-repetition mechanism. Every generated post is
    stored with the topic it covered and a fingerprint of its wording; the next
    generation gets the recent topics as an explicit "already covered, pick
    something else" list, and the fingerprint catches the case where the model
    invents a fresh-looking topic label but writes the same post again.
    """
    KIND_FACT = 'fact'
    KIND_PROMO = 'promo'
    KIND_CHOICES = [
        (KIND_FACT, 'Интересный факт'),
        (KIND_PROMO, 'Промо бота'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_PUBLISHED, 'Опубликован'),
        (STATUS_FAILED, 'Ошибка отправки'),
    ]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_FACT)
    # Short human-readable label of what the post is about ("Башня как
    # освобождение", "происхождение слова футарк"). Fed back to the model as the
    # do-not-repeat list, so it carries more weight than it looks.
    topic = models.CharField(max_length=200)
    text = models.TextField()
    # Hash of the post's significant words — see channel.fingerprint(). Two posts
    # with the same fingerprint say the same thing even if their topics differ.
    fingerprint = models.CharField(max_length=64, db_index=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    tg_message_id = models.BigIntegerField(null=True, blank=True)
    error = models.TextField(blank=True)

    # Cost visibility: these runs are the only scheduled spend on the API.
    model_used = models.CharField(max_length=64, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['kind', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'[{self.get_kind_display()}] {self.topic} — {self.get_status_display()}'

