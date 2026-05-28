"""Numerology — stored readings + AI interpretations."""
from django.conf import settings
from django.db import models


class NumerologyInterpretation(models.Model):
    body_md = models.TextField()
    model_used = models.CharField(max_length=64)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"NumerologyInterpretation #{self.pk}"


class NumerologyReading(models.Model):
    LOCALE_CHOICES = [("ru", "Russian"), ("en", "English")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="numerology_readings",
    )
    full_name = models.CharField(max_length=128)
    birth_date = models.DateField()
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES, default="ru")

    life_path = models.PositiveSmallIntegerField()
    destiny = models.PositiveSmallIntegerField()
    soul_urge = models.PositiveSmallIntegerField()
    personality = models.PositiveSmallIntegerField()
    birthday = models.PositiveSmallIntegerField()

    interpretation = models.OneToOneField(
        NumerologyInterpretation,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="reading",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"NumerologyReading #{self.pk} ({self.full_name})"
