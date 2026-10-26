"""The Django account behind a Telegram profile."""
from __future__ import annotations

from django.contrib.auth import get_user_model


def ensure_user(tg_profile):
    """Return the linked account, creating it on first need.

    The convention (tg_<id>@telegram.local) matches the Mini App sign-in, so the
    person lands in the same account when they later open the app.
    """
    if tg_profile.user_id is not None:
        return tg_profile.user
    User = get_user_model()
    email = f'tg_{tg_profile.tg_id}@telegram.local'
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'display_name': tg_profile.tg_first_name or f'tg_{tg_profile.tg_id}',
            'is_active': True,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])
    tg_profile.user = user
    tg_profile.save(update_fields=['user'])
    return user
