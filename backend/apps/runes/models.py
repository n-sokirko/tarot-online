"""Elder Futhark runes — owned by database-agent. Parallels apps.readings."""
from django.conf import settings
from django.db import models


class Rune(models.Model):
    slug = models.SlugField(unique=True, max_length=32)
    number = models.PositiveSmallIntegerField(unique=True)  # 1..24
    aett = models.PositiveSmallIntegerField()  # 1, 2 or 3 (Freyr / Heimdall / Tyr)
    symbol = models.CharField(max_length=4)  # ᚠ ᚢ ᚦ ...

    name_ru = models.CharField(max_length=64)
    name_en = models.CharField(max_length=64)
    meaning_ru = models.TextField()
    meaning_en = models.TextField()
    keywords_ru = models.JSONField(default=list)
    keywords_en = models.JSONField(default=list)

    class Meta:
        ordering = ['number']

    def __str__(self) -> str:
        return f'{self.symbol} {self.name_en}'


class RuneCast(models.Model):
    LOCALE_CHOICES = [('ru', 'Russian'), ('en', 'English')]
    LAYOUT_CHOICES = [
        ('single', 'Single rune'),
        ('three', 'Three runes'),
        ('five', 'Five runes (cross)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='rune_casts',
    )
    layout = models.CharField(max_length=8, choices=LAYOUT_CHOICES, default='three')
    question = models.TextField()
    locale = models.CharField(max_length=2, choices=LOCALE_CHOICES, default='ru')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]


class RuneCastItem(models.Model):
    cast = models.ForeignKey(RuneCast, on_delete=models.CASCADE, related_name='items')
    rune = models.ForeignKey(Rune, on_delete=models.PROTECT)
    position_index = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('cast', 'position_index')
        ordering = ['position_index']


class RuneInterpretation(models.Model):
    cast = models.OneToOneField(RuneCast, on_delete=models.CASCADE, related_name='interpretation')
    body_md = models.TextField()
    model_used = models.CharField(max_length=64)
    prompt_version = models.CharField(max_length=32)
    generated_at = models.DateTimeField(auto_now_add=True)
    token_count = models.PositiveIntegerField(default=0)
