"""Birth-date resolution shared by the bot handlers and the daily push command.

Django models only (no telegram import), so the management command can load
without the python-telegram-bot stack installed.
"""
import datetime


def natal_birth_date(telegram_user) -> datetime.date | None:
    """Birth date from the user's most recent natal chart, if any."""
    if not telegram_user.user_id:
        return None
    from apps.natal.models import NatalChart
    chart = (
        NatalChart.objects
        .filter(user_id=telegram_user.user_id)
        .order_by('-created_at')
        .first()
    )
    return chart.birth_date if chart else None
