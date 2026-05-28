"""Models for the natal chart module.

NatalInterpretation must be defined before NatalChart because NatalChart
holds a nullable FK to it (OneToOneField with SET_NULL requires the target
to exist first in the module).
"""
from django.conf import settings
from django.db import models


class NatalInterpretation(models.Model):
    """AI-generated narrative for a natal chart."""

    body_md = models.TextField()
    model_used = models.CharField(max_length=64)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"NatalInterpretation #{self.pk}"


class NatalChart(models.Model):
    """Stored natal chart — persists both the input data and calculated output."""

    LOCALE_CHOICES = [("ru", "Russian"), ("en", "English")]

    # --- who ---
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="natal_charts",
    )

    # --- birth input ---
    birth_name = models.CharField(max_length=128, blank=True)
    birth_date = models.DateField()
    birth_time = models.TimeField(null=True, blank=True)  # absent → no houses
    birth_city = models.CharField(max_length=128)
    birth_lat = models.FloatField()
    birth_lng = models.FloatField()
    birth_tz = models.CharField(max_length=64)  # "Europe/Moscow"
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES, default="ru")

    # --- calculated output (JSON blobs) ---
    planets = models.JSONField()  # list of planet dicts
    houses = models.JSONField(default=list)   # house cusp dicts (empty if no birth_time)
    aspects = models.JSONField(default=list)  # aspect dicts

    ascendant = models.FloatField(null=True, blank=True)  # degrees 0-360

    # --- AI interpretation ---
    interpretation = models.OneToOneField(
        NatalInterpretation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chart",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"NatalChart #{self.pk} ({self.birth_name or self.birth_city})"
