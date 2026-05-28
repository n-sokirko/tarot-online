"""NatalConfig — Django app config for the natal chart module."""
from django.apps import AppConfig


class NatalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.natal"
    label = "natal"
    verbose_name = "Natal Charts"
