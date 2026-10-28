"""Consent to the Terms and Privacy Policy in the bot's /start."""
import asyncio
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.telegram_bot import handlers
from apps.telegram_bot.models import TelegramUser

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _gate_off(settings):
    settings.TELEGRAM_REQUIRED_CHANNEL = ''        # the channel gate is not what is tested here
    settings.LEGAL_VERSION = '2026-10-28'
    settings.WEBAPP_URL = 'https://example.com'


def _update(tg_id=7, lang='ru', args=None):
    user = MagicMock()
    user.id, user.username, user.first_name, user.language_code = tg_id, 'u', 'U', lang
    update = MagicMock()
    update.effective_user = user
    update.message.reply_text = AsyncMock()
    ctx = MagicMock()
    ctx.args, ctx.user_data = args or [], {}
    return update, ctx


def _callback(tg_id=7, lang='ru'):
    update, ctx = _update(tg_id, lang)
    q = MagicMock()
    q.from_user = update.effective_user
    q.answer = AsyncMock()
    q.edit_message_text = AsyncMock()
    q.message.reply_text = AsyncMock()
    update.callback_query = q
    return update, ctx, q


class TestStartAsksFirst:
    def test_a_new_person_gets_the_consent_screen_not_the_menu(self):
        update, ctx = _update()
        asyncio.run(handlers.start(update, ctx))
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.await_args.args[0]
        kwargs = update.message.reply_text.await_args.kwargs
        assert 'Условия использования' in text and 'от 16 лет' in text
        rows = kwargs['reply_markup'].inline_keyboard
        assert rows[0][0].url == 'https://example.com/terms'
        assert rows[0][1].url == 'https://example.com/privacy'
        assert rows[1][0].callback_data == handlers.TERMS_ACCEPT_DATA
        assert 'Tarot Online Bot' not in text                # the menu has not been shown

    def test_english_speakers_get_it_in_english(self):
        update, ctx = _update(lang='en')
        asyncio.run(handlers.start(update, ctx))
        assert 'Terms of Service' in update.message.reply_text.await_args.args[0]

    def test_someone_who_accepted_the_current_wording_goes_straight_to_the_menu(self):
        TelegramUser.objects.create(tg_id=7, terms_accepted_at='2026-10-28T10:00:00Z',
                                    terms_version='2026-10-28')
        update, ctx = _update()
        asyncio.run(handlers.start(update, ctx))
        assert 'Tarot Online Bot' in update.message.reply_text.await_args.args[0]

    def test_a_new_wording_asks_again(self, settings):
        TelegramUser.objects.create(tg_id=7, terms_accepted_at='2026-01-01T10:00:00Z',
                                    terms_version='2026-01-01')
        update, ctx = _update()
        asyncio.run(handlers.start(update, ctx))
        assert 'Перед началом' in update.message.reply_text.await_args.args[0]

    def test_payment_and_contest_links_are_never_held_up(self):
        update, ctx = _update(args=['buy_sometoken'])
        with patch.object(handlers, '_handle_buy', new=AsyncMock()) as buy:
            asyncio.run(handlers.start(update, ctx))
        buy.assert_awaited_once()
        update.message.reply_text.assert_not_awaited()       # no consent screen in the way


class TestAccept:
    def test_accepting_records_it_and_continues_to_the_menu(self):
        update, ctx, q = _callback()
        asyncio.run(handlers.terms_accept_callback(update, ctx))
        profile = TelegramUser.objects.get(tg_id=7)
        assert profile.terms_accepted_at is not None
        assert profile.terms_version == '2026-10-28'
        q.edit_message_text.assert_awaited_once()
        assert 'Tarot Online Bot' in q.message.reply_text.await_args.args[0]

    def test_it_is_also_kept_on_the_linked_account_once(self, django_user_model):
        user = django_user_model.objects.create_user(username='t', email='t@e.com', password='x')
        TelegramUser.objects.create(tg_id=7, user=user)
        update, ctx, _ = _callback()
        asyncio.run(handlers.terms_accept_callback(update, ctx))
        user.refresh_from_db()
        assert user.terms_accepted_at is not None and user.terms_version == '2026-10-28'

    def test_after_accepting_start_no_longer_asks(self):
        update, ctx, _ = _callback()
        asyncio.run(handlers.terms_accept_callback(update, ctx))
        again, ctx2 = _update()
        asyncio.run(handlers.start(again, ctx2))
        assert 'Tarot Online Bot' in again.message.reply_text.await_args.args[0]

    def test_a_failed_edit_does_not_stop_the_menu(self):
        update, ctx, q = _callback()
        q.edit_message_text.side_effect = RuntimeError('message is not modified')
        asyncio.run(handlers.terms_accept_callback(update, ctx))
        q.message.reply_text.assert_awaited_once()


def test_backend_and_website_agree_on_the_wording(settings):
    """People accept a wording; the bot and the site must name the same one."""
    config = Path(__file__).resolve().parents[4] / 'frontend' / 'lib' / 'legal' / 'config.ts'
    match = re.search(r"version:\s*'([^']+)'", config.read_text(encoding='utf-8'))
    assert match, 'frontend/lib/legal/config.ts has no version'
    from django.conf import settings as real
    assert match.group(1) == real.LEGAL_VERSION
