"""URL config for the telegram_bot app."""
from django.urls import path

from apps.telegram_bot.views import ChannelBriefView, ChannelPublishView, TelegramWebhookView

urlpatterns = [
    path('telegram/webhook/', TelegramWebhookView.as_view(), name='telegram-webhook'),
    # Used by the scheduled Claude Code routine that writes the channel posts.
    path('channel/brief/', ChannelBriefView.as_view(), name='channel-brief'),
    path('channel/publish/', ChannelPublishView.as_view(), name='channel-publish'),
]
