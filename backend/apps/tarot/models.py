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
