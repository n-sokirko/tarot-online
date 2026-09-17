"""URL config for the telegram_bot app."""
from django.urls import path

from apps.telegram_bot.views import TelegramWebhookView

urlpatterns = [
    path('telegram/webhook/', TelegramWebhookView.as_view(), name='telegram-webhook'),
]
