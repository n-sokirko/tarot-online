"""Custom user model — owned by database-agent."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    LOCALE_CHOICES = [('ru', 'Russian'), ('en', 'English')]

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=64, blank=True)
    locale = models.CharField(max_length=2, choices=LOCALE_CHOICES, default='ru')
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [models.Index(fields=['email'])]
