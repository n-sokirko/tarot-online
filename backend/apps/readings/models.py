"""Reading session models. Owned by database-agent."""
from django.conf import settings
from django.db import models


class Reading(models.Model):
    LOCALE_CHOICES = [('ru', 'Russian'), ('en', 'English')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='readings',
    )
    spread_type = models.ForeignKey('tarot.SpreadType', on_delete=models.PROTECT)
    question = models.TextField()
    locale = models.CharField(max_length=2, choices=LOCALE_CHOICES, default='ru')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at']), models.Index(fields=['user', '-created_at'])]


class ReadingCard(models.Model):
    reading = models.ForeignKey(Reading, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey('tarot.Card', on_delete=models.PROTECT)
    position_index = models.PositiveSmallIntegerField()
    is_reversed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('reading', 'position_index')


class Interpretation(models.Model):
    reading = models.OneToOneField(Reading, on_delete=models.CASCADE, related_name='interpretation')
    body_md = models.TextField()
    model_used = models.CharField(max_length=64)
    prompt_version = models.CharField(max_length=32)
    generated_at = models.DateTimeField(auto_now_add=True)
    token_count = models.PositiveIntegerField(default=0)
