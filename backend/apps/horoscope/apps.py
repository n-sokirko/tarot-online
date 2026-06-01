"""Horoscope Django app config."""
from django.apps import AppConfig


class HoroscopeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.horoscope"
    label = "horoscope"
    verbose_name = "Daily Horoscope"
