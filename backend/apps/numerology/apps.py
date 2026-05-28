"""Numerology Django app config."""
from django.apps import AppConfig


class NumerologyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.numerology"
    label = "numerology"
    verbose_name = "Numerology"
