"""Horoscope — cached AI deep readings per (sign, date, locale).

The free deterministic daily horoscope is computed on the fly and not stored.
Only the premium AI-written reading is persisted, so we don't pay the model
twice for the same sign on the same day.
"""
from django.db import models


class HoroscopeAIReading(models.Model):
    LOCALE_CHOICES = [("ru", "Russian"), ("en", "English")]

    sign = models.CharField(max_length=16)
    date = models.DateField()
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES, default="ru")

    body_md = models.TextField()
    model_used = models.CharField(max_length=64)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sign", "date", "locale"],
                name="uniq_horoscope_sign_date_locale",
            )
        ]
        indexes = [models.Index(fields=["sign", "date", "locale"])]

    def __str__(self) -> str:
        return f"HoroscopeAIReading({self.sign}, {self.date}, {self.locale})"
