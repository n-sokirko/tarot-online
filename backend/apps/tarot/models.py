"""Tarot domain models — owned by database-agent. Do not edit without consulting it."""
from django.db import models


class Card(models.Model):
    SUIT_CHOICES = [
        ('major', 'Major Arcana'),
        ('cups', 'Cups'),
        ('wands', 'Wands'),
        ('swords', 'Swords'),
        ('pentacles', 'Pentacles'),
    ]

    slug = models.SlugField(unique=True, max_length=64)
    suit = models.CharField(max_length=16, choices=SUIT_CHOICES)
    number = models.PositiveSmallIntegerField()

    name_ru = models.CharField(max_length=128)
    name_en = models.CharField(max_length=128)

    upright_meaning_ru = models.TextField()
    upright_meaning_en = models.TextField()
    reversed_meaning_ru = models.TextField()
    reversed_meaning_en = models.TextField()

    keywords_ru = models.JSONField(default=list)
    keywords_en = models.JSONField(default=list)

    image_url = models.CharField(max_length=255)

    class Meta:
        ordering = ['suit', 'number']
        indexes = [models.Index(fields=['suit', 'number'])]

    def __str__(self) -> str:
        return f'{self.name_en} ({self.slug})'


class SpreadType(models.Model):
    slug = models.SlugField(unique=True, max_length=64)
    name_ru = models.CharField(max_length=128)
    name_en = models.CharField(max_length=128)
    positions_count = models.PositiveSmallIntegerField()
    positions = models.JSONField(default=list)  # [{index, label_ru, label_en, meaning_ru, meaning_en}]

    def __str__(self) -> str:
        return self.name_en


class RitualDay(models.Model):
    """One day on which the person opened their card of the day.

    The daily ritual on the home screen ("7 дней", the week grid) is built from
    these rows, so it survives a device change — a streak kept in the browser
    would reset the moment someone opens the Mini App on another phone.

    `day` is the person's own calendar date, not the server's: the server runs
    on UTC and most of the audience on UTC+3, so a server-side "today" would put
    a 1 a.m. visit in Minsk on the previous day and break the streak.
    """
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='ritual_days')
    day = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'day'], name='ritual_day_once'),
        ]
        indexes = [models.Index(fields=['user', '-day'])]

    def __str__(self) -> str:
        return f'{self.user_id} @ {self.day}'
