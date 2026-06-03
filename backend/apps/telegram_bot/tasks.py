"""Celery tasks for the Telegram bot."""
from celery import shared_task
from django.core.management import call_command


@shared_task
def send_daily_push() -> str:
    """Daily card-of-the-day push to subscribed users (scheduled via Celery beat)."""
    call_command("send_daily_push")
    return "ok"
