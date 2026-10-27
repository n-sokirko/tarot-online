"""Who a broadcast did not reach, and why."""
from unittest.mock import MagicMock, patch

import pytest
from django.contrib import admin as dj_admin
from django.test import RequestFactory

from apps.telegram_bot import delivery
from apps.telegram_bot.admin import BroadcastAdmin, TelegramUserAdmin
from apps.telegram_bot.models import Broadcast, TelegramUser

pytestmark = pytest.mark.django_db

BLOCKED = 'Forbidden: bot was blocked by the user'
NEVER_STARTED = "Forbidden: bot can't initiate conversation with a user"
NO_CHAT = 'Bad Request: chat not found'


def _reply(ok: bool, description: str = '', status: int = 200):
    r = MagicMock()
    r.ok = ok
    r.status_code = status
    r.json.return_value = {'ok': ok, 'description': description}
    return r


class TestExplain:
    @pytest.mark.parametrize('text,expected', [
        (BLOCKED, 'заблокировал бота'),
        (NEVER_STARTED, 'не запускал бота (/start)'),
        (NO_CHAT, 'чат не найден (не запускал бота)'),
        ('Forbidden: user is deactivated', 'аккаунт удалён'),
        ('something odd', 'something odd'),
        ('', 'неизвестная ошибка'),
    ])
    def test_reasons_are_readable(self, text, expected):
        assert delivery.explain(text) == expected

    @pytest.mark.parametrize('text,permanent', [
        (BLOCKED, True), (NEVER_STARTED, True), (NO_CHAT, True),
        ('Too Many Requests: retry after 5', False),
        ("Bad Request: can't parse entities", False),
    ])
    def test_only_permanent_refusals_mark_a_person_unreachable(self, text, permanent):
        assert delivery.is_permanent(text) is permanent


class TestRecord:
    def test_blocked_person_is_flagged_and_unflagged_on_success(self):
        u = TelegramUser.objects.create(tg_id=1)
        delivery.record(u, False, BLOCKED)
        u.refresh_from_db()
        assert u.bot_blocked is True and u.last_send_error == 'заблокировал бота'
        delivery.record(u, True)
        u.refresh_from_db()
        assert u.bot_blocked is False and u.last_send_error == ''

    def test_a_temporary_error_does_not_mark_anyone_blocked(self):
        u = TelegramUser.objects.create(tg_id=1)
        delivery.record(u, False, 'Too Many Requests: retry after 5')
        u.refresh_from_db()
        assert u.bot_blocked is False and u.last_send_error.startswith('Too Many')

    def test_network_failure_is_a_failure_not_a_crash(self):
        with patch('apps.telegram_bot.delivery.requests.post', side_effect=ConnectionError('x')):
            ok, err = delivery.send_text('t', 1, 'hi')
        assert ok is False and 'сеть' in err


def _by_chat(mapping):
    """requests.post stub: reply depends on the chat id in the JSON body."""
    def post(url, json=None, timeout=None):
        return mapping[json['chat_id']]
    return post


class TestBroadcastAdmin:
    def _run(self, bc, mapping, settings):
        settings.TELEGRAM_BOT_TOKEN = 'tok'
        model_admin = BroadcastAdmin(Broadcast, dj_admin.site)
        model_admin.message_user = MagicMock()
        request = RequestFactory().post('/')
        with patch('apps.telegram_bot.delivery.requests.post', side_effect=_by_chat(mapping)):
            model_admin.send_now(request, Broadcast.objects.filter(pk=bc.pk))
        bc.refresh_from_db()
        return model_admin

    def test_records_who_did_not_get_it_and_why(self, settings):
        TelegramUser.objects.create(tg_id=1, tg_username='ok_user')
        TelegramUser.objects.create(tg_id=2, tg_username='blocker')
        TelegramUser.objects.create(tg_id=3, tg_first_name='Новичок')
        bc = Broadcast.objects.create(title='t', message='привет')

        self._run(bc, {1: _reply(True), 2: _reply(False, BLOCKED, 403),
                       3: _reply(False, NEVER_STARTED, 403)}, settings)

        assert (bc.sent_count, bc.failed_count) == (1, 2)
        assert '2 @blocker: заблокировал бота' in bc.failed_detail
        assert '3 @Новичок: не запускал бота (/start)' in bc.failed_detail
        assert '1 @ok_user' not in bc.failed_detail
        assert TelegramUser.objects.get(tg_id=2).bot_blocked is True
        assert TelegramUser.objects.get(tg_id=1).bot_blocked is False

    def test_a_blocked_person_who_comes_back_is_unflagged(self, settings):
        TelegramUser.objects.create(tg_id=1, bot_blocked=True, last_send_error='заблокировал бота')
        bc = Broadcast.objects.create(title='t', message='привет')
        self._run(bc, {1: _reply(True)}, settings)
        assert TelegramUser.objects.get(tg_id=1).bot_blocked is False

    def test_subscribers_only_target_skips_the_rest(self, settings):
        TelegramUser.objects.create(tg_id=1, daily_push=True)
        TelegramUser.objects.create(tg_id=2, daily_push=False)
        bc = Broadcast.objects.create(title='t', message='x', target=Broadcast.TARGET_SUBSCRIBERS)
        self._run(bc, {1: _reply(True)}, settings)   # a call for tg 2 would KeyError
        assert bc.sent_count == 1


class TestReachabilityCheck:
    def test_probe_flags_the_unreachable_without_sending_a_message(self, settings):
        settings.TELEGRAM_BOT_TOKEN = 'tok'
        TelegramUser.objects.create(tg_id=1)
        TelegramUser.objects.create(tg_id=2)
        calls = []

        def post(url, json=None, timeout=None):
            calls.append((url.rsplit('/', 1)[-1], json))
            return _reply(True) if json['chat_id'] == 1 else _reply(False, NEVER_STARTED, 403)

        model_admin = TelegramUserAdmin(TelegramUser, dj_admin.site)
        model_admin.message_user = MagicMock()
        with patch('apps.telegram_bot.delivery.requests.post', side_effect=post):
            model_admin.check_reachable(RequestFactory().post('/'), TelegramUser.objects.all())

        assert {c[0] for c in calls} == {'sendChatAction'}        # nothing the person can read
        assert TelegramUser.objects.get(tg_id=2).bot_blocked is True
        assert TelegramUser.objects.get(tg_id=1).bot_blocked is False
        assert 'не доходит: 1' in model_admin.message_user.call_args.args[1]
