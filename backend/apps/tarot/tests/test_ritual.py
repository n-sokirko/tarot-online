"""The daily ritual: streak counting, the week grid and the date guard."""
import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.tarot.models import RitualDay
from apps.tarot.ritual import streak_for

D = datetime.date
TODAY = D(2026, 9, 21)  # a Monday


class TestStreak:
    def test_counts_back_from_today_when_done(self):
        done = {TODAY, TODAY - datetime.timedelta(1), TODAY - datetime.timedelta(2)}
        assert streak_for(done, TODAY) == 3

    def test_still_alive_before_today_is_done(self):
        """Six days kept and today not opened yet is a six-day streak, not zero."""
        done = {TODAY - datetime.timedelta(i) for i in range(1, 7)}
        assert streak_for(done, TODAY) == 6

    def test_a_gap_ends_it(self):
        done = {TODAY, TODAY - datetime.timedelta(2)}
        assert streak_for(done, TODAY) == 1

    def test_nothing_done(self):
        assert streak_for(set(), TODAY) == 0


@pytest.fixture
def user(django_user_model, db):
    return django_user_model.objects.create_user(
        username='ritual', email='ritual@example.com', password='pw')


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def _server_now(day: D):
    return timezone.make_aware(datetime.datetime(day.year, day.month, day.day, 12))


@pytest.mark.django_db
class TestEndpoints:
    def test_requires_sign_in(self):
        assert APIClient().get('/api/v1/ritual/').status_code in (401, 403)

    def test_checkin_marks_today_and_is_idempotent(self, client, user):
        with patch('apps.tarot.ritual.timezone.now', return_value=_server_now(TODAY)):
            first = client.post('/api/v1/ritual/checkin/', {'today': '2026-09-21'}, format='json')
            second = client.post('/api/v1/ritual/checkin/', {'today': '2026-09-21'}, format='json')
        assert first.status_code == 200 and second.status_code == 200
        assert second.json()['done_today'] is True
        assert second.json()['streak'] == 1
        assert RitualDay.objects.filter(user=user).count() == 1

    def test_week_runs_monday_to_sunday(self, client, user):
        RitualDay.objects.create(user=user, day=TODAY)
        with patch('apps.tarot.ritual.timezone.now', return_value=_server_now(TODAY)):
            body = client.get('/api/v1/ritual/', {'today': '2026-09-21'}).json()
        week = body['week']
        assert len(week) == 7
        assert week[0]['date'] == '2026-09-21' and week[0]['weekday'] == 0
        assert week[0]['done'] and week[0]['is_today']
        assert all(d['is_future'] for d in week[1:])

    def test_uses_the_clients_date_across_midnight(self, client, user):
        """01:00 in Minsk is still the previous day on the UTC server; the
        person's own date is what counts."""
        with patch('apps.tarot.ritual.timezone.now', return_value=_server_now(TODAY)):
            body = client.post('/api/v1/ritual/checkin/', {'today': '2026-09-22'},
                               format='json').json()
        assert body['today'] == '2026-09-22'
        assert RitualDay.objects.get(user=user).day == D(2026, 9, 22)

    def test_refuses_a_date_far_from_the_servers(self, client):
        """Back-filling last week to fake a streak must not work."""
        with patch('apps.tarot.ritual.timezone.now', return_value=_server_now(TODAY)):
            resp = client.post('/api/v1/ritual/checkin/', {'today': '2026-09-14'}, format='json')
        assert resp.status_code == 400

    def test_refuses_garbage(self, client):
        assert client.get('/api/v1/ritual/', {'today': 'yesterday'}).status_code == 400
