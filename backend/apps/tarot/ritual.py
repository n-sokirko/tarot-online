"""The daily ritual: opening the card of the day, day after day.

GET  /api/v1/ritual/?today=YYYY-MM-DD           — streak and this week's grid
POST /api/v1/ritual/checkin/  {"today": "..."}  — mark today as done

Both take the person's own calendar date (see RitualDay for why) and only
accept one within a day of the server's, so a streak cannot be back-filled.
Signed-in users only; the home screen keeps an anonymous visitor's streak in the
browser, since there is nobody to attach it to.
"""
from __future__ import annotations

import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tarot.models import RitualDay

# How far the client's "today" may drift from the server's UTC date. One day
# covers every real time zone (UTC-12 .. UTC+14) without letting anyone mark a
# week they skipped.
MAX_DRIFT_DAYS = 1


def _client_today(raw: str | None) -> datetime.date | None:
    """The person's date, or None if it is missing, malformed or implausible."""
    server_today = timezone.now().date()
    if not raw:
        return server_today
    try:
        day = datetime.date.fromisoformat(raw)
    except ValueError:
        return None
    if abs((day - server_today).days) > MAX_DRIFT_DAYS:
        return None
    return day


def streak_for(done: set[datetime.date], today: datetime.date) -> int:
    """Consecutive days ending today — or yesterday, if today isn't done yet.

    A streak is still alive until the day actually ends: someone who kept it
    for six days and hasn't opened today's card yet is on a six-day streak, not
    back at zero.
    """
    cursor = today if today in done else today - datetime.timedelta(days=1)
    count = 0
    while cursor in done:
        count += 1
        cursor -= datetime.timedelta(days=1)
    return count


def ritual_state(user, today: datetime.date) -> dict:
    # Enough history for any streak worth showing, without scanning forever.
    since = today - datetime.timedelta(days=366)
    done = set(
        RitualDay.objects.filter(user=user, day__gte=since, day__lte=today)
        .values_list('day', flat=True)
    )
    monday = today - datetime.timedelta(days=today.weekday())
    week = []
    for i in range(7):
        d = monday + datetime.timedelta(days=i)
        week.append({
            'date': d.isoformat(),
            'weekday': i,  # 0 = Monday
            'done': d in done,
            'is_today': d == today,
            'is_future': d > today,
        })
    return {
        'today': today.isoformat(),
        'done_today': today in done,
        'streak': streak_for(done, today),
        'week': week,
    }


class RitualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = _client_today(request.query_params.get('today'))
        if today is None:
            return Response({'detail': 'bad or implausible date'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(ritual_state(request.user, today))


class RitualCheckinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = _client_today(request.data.get('today'))
        if today is None:
            return Response({'detail': 'bad or implausible date'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Idempotent: flipping the card twice in a day is one ritual, not two.
        try:
            with transaction.atomic():
                RitualDay.objects.get_or_create(user=request.user, day=today)
        except IntegrityError:
            pass  # a concurrent request got there first — same outcome
        return Response(ritual_state(request.user, today))
