"""Custom user model — owned by database-agent."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    LOCALE_CHOICES = [('ru', 'Russian'), ('en', 'English')]

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=64, blank=True)
    locale = models.CharField(max_length=2, choices=LOCALE_CHOICES, default='ru')
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Consent to the Terms of Service and Privacy Policy: when it was given and
    # which wording it was given to (the frontend's LEGAL_CONFIG.version). Null for
    # accounts made before the documents existed, and for Telegram sign-ups that
    # have not accepted them in the bot yet.
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=16, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [models.Index(fields=['email'])]
