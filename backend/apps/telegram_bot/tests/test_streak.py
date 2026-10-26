"""The bot's card-of-the-day streak: counting, check-in, and the push message."""
import datetime
from unittest.mock import patch

import pytest

from apps.tarot.models import Card, RitualDay
from apps.telegram_bot import push, streak
from apps.telegram_bot.models import TelegramUser

TODAY = datetime.date(2026, 10, 27)
D = datetime.timedelta


@pytest.fixture(autouse=True)
def _fixed_today():
    with patch('apps.telegram_bot.streak.bot_today', return_value=TODAY), \
         patch('apps.telegram_bot.push.bot_today', create=True, return_value=TODAY):
        yield


@pytest.fixture
def card(db):
    return Card.objects.create(
        slug='the-tower', suit='major', number=16,
        name_ru='Башня', name_en='The Tower',
        upright_meaning_ru='Внезапное разрушение. Старое рушится. Это освобождает место. Дальше ещё текст.',
        upright_meaning_en='Sudden upheaval. The old falls. It makes room.',
        reversed_meaning_ru='Разрушение, которого удалось избежать.',
        reversed_meaning_en='Upheaval avoided.',
        keywords_ru=['перемены', 'правда', 'освобождение'],
        keywords_en=['change', 'truth', 'release'],
        image_url='/cards/16.jpg',
    )


@pytest.fixture
def tg(db):
    return TelegramUser.objects.create(tg_id=111, tg_first_name='Аня', locale='ru')


class TestDaysRu:
    @pytest.mark.parametrize('n,expected', [
        (1, '1 день'), (2, '2 дня'), (4, '4 дня'), (5, '5 дней'),
        (11, '11 дней'), (12, '12 дней'), (21, '21 день'), (22, '22 дня'), (111, '111 дней'),
    ])
    def test_plural_forms(self, n, expected):
        assert streak.days_ru(n) == expected


@pytest.mark.django_db
class TestCheckIn:
    def test_unlinked_person_has_no_streak(self, tg):
        assert streak.current_streak(tg) == (0, False)
        assert RitualDay.objects.count() == 0  # looking must not create anything

    def test_first_check_in_creates_account_and_starts_streak(self, tg):
        count, new = streak.check_in(tg)
        assert (count, new) == (1, True)
        tg.refresh_from_db()
        assert tg.user.email == 'tg_111@telegram.local'
        assert RitualDay.objects.get(user=tg.user).day == TODAY

    def test_second_tap_same_day_changes_nothing(self, tg):
        streak.check_in(tg)
        count, new = streak.check_in(tg)
        assert (count, new) == (1, False)
        assert RitualDay.objects.count() == 1

    def test_consecutive_days_build_a_streak(self, tg):
        streak.check_in(tg)
        for back in (1, 2):
            RitualDay.objects.create(user=tg.user, day=TODAY - D(days=back))
        assert streak.current_streak(tg) == (3, True)

    def test_yesterdays_streak_survives_until_today_is_marked(self, tg):
        streak.check_in(tg)
        RitualDay.objects.filter(user=tg.user).update(day=TODAY - D(days=1))
        assert streak.current_streak(tg) == (1, False)

    def test_a_gap_breaks_the_streak(self, tg):
        streak.check_in(tg)
        RitualDay.objects.filter(user=tg.user).update(day=TODAY - D(days=3))
        assert streak.current_streak(tg) == (0, False)

    def test_it_is_the_same_streak_as_the_website(self, tg):
        """The Mini App signs in with the same tg_<id>@telegram.local account, so
        a day marked on the site shows up in the bot."""
        streak.check_in(tg)
        user = tg.user
        RitualDay.objects.create(user=user, day=TODAY - D(days=1))  # "from the site"
        assert streak.current_streak(tg)[0] == 2


class TestSnippet:
    def test_keeps_whole_sentences_within_the_limit(self):
        text = 'Первая мысль. Вторая мысль. ' + 'Слово ' * 80
        out = push._snippet(text, limit=60)
        assert out.endswith('.') and len(out) <= 60

    def test_short_text_is_untouched(self):
        assert push._snippet('Коротко.') == 'Коротко.'

    def test_markdown_breakers_are_removed(self):
        assert push._snippet('a_b *c* `d` [e]') == 'ab c d e'


@pytest.mark.django_db
class TestMessage:
    def test_message_has_meaning_and_streak_line(self, card):
        text, open_btn, checkin_btn = push.card_message(
            card, is_ru=True, is_reversed=False, streak=4, done_today=False)
        assert 'Башня' in text
        assert 'Внезапное разрушение.' in text           # value is in the message itself
        assert 'Серия: 4 дня' in text
        assert 'Отметить день' in checkin_btn

    def test_no_streak_invites_to_start_one(self, card):
        text, *_ = push.card_message(card, is_ru=True, is_reversed=False)
        assert 'начать серию' in text

    def test_english_variant(self, card):
        text, open_btn, _ = push.card_message(
            card, is_ru=False, is_reversed=True, streak=1, done_today=False)
        assert '*The Tower* (reversed)' in text
        assert 'Streak: 1 day.' in text

    def test_markup_switches_to_done_state(self):
        fresh = push.card_markup(webapp='https://x', open_label='o', checkin_label='c')
        done = push.card_markup(webapp='https://x', open_label='o', checkin_label='c', done=True)
        assert fresh['inline_keyboard'][0][0]['callback_data'] == push.CHECKIN_DATA
        assert done['inline_keyboard'][0][0]['callback_data'] == push.DONE_DATA
        assert fresh['inline_keyboard'][1][0]['web_app']['url'] == 'https://x'


@pytest.mark.django_db
class TestPush:
    def test_push_carries_the_checkin_button_and_streak(self, card, tg, settings):
        settings.TELEGRAM_BOT_TOKEN = 't'
        streak.check_in(tg)
        RitualDay.objects.create(user=tg.user, day=TODAY - D(days=1))
        RitualDay.objects.filter(user=tg.user, day=TODAY).delete()  # today not done yet

        with patch('apps.telegram_bot.push._send', return_value=True) as send:
            result = push.send_card_push([tg])

        assert result == {'sent': 1, 'failed': 0}
        _token, chat_id, text, markup = send.call_args.args
        assert chat_id == 111
        assert 'Серия: 1 день' in text
        assert markup['inline_keyboard'][0][0]['callback_data'] == push.CHECKIN_DATA

    def test_same_card_for_the_push_and_the_button(self, card, tg):
        """Tapping the button must re-render the card the push showed."""
        a, _ = push.render_card(tg, [card])
        b, _ = push.render_card(tg, [card], streak=5, done_today=True)
        assert a.split('\n\n')[1] == b.split('\n\n')[1]


class TestKeyboardConversion:
    def test_dict_keyboard_becomes_a_ptb_keyboard(self):
        from telegram import InlineKeyboardMarkup

        from apps.telegram_bot.handlers import _to_inline_markup

        data = push.card_markup(webapp='https://example.com', open_label='open',
                                checkin_label='mark')
        kb = _to_inline_markup(data)
        assert isinstance(kb, InlineKeyboardMarkup)
        mark, open_ = kb.inline_keyboard[0][0], kb.inline_keyboard[1][0]
        assert mark.callback_data == push.CHECKIN_DATA and mark.web_app is None
        assert open_.web_app.url == 'https://example.com' and open_.callback_data is None


@pytest.mark.django_db(transaction=True)
class TestCheckinButtonEndToEnd:
    """The real handler against a fake Telegram: tap → streak → message edited."""

    def _update(self, tg_id=111, lang='ru'):
        from unittest.mock import AsyncMock, MagicMock

        q = MagicMock()
        q.from_user.id = tg_id
        q.from_user.username = 'anya'
        q.from_user.first_name = 'Аня'
        q.from_user.language_code = lang
        q.answer = AsyncMock()
        q.edit_message_text = AsyncMock()
        update = MagicMock()
        update.callback_query = q
        return update, q

    def test_tap_marks_the_day_and_rewrites_the_message(self, card, settings):
        import asyncio

        from apps.telegram_bot.handlers import ritual_checkin_callback

        update, q = self._update()
        asyncio.run(ritual_checkin_callback(update, None))

        q.answer.assert_awaited_once()
        assert 'Серия: 1 день' in q.answer.await_args.kwargs['text']
        q.edit_message_text.assert_awaited_once()
        text = q.edit_message_text.await_args.args[0]
        assert 'День отмечен' in text and 'Башня' in text
        assert q.edit_message_text.await_args.kwargs['parse_mode'] == 'Markdown'
        assert RitualDay.objects.count() == 1

    def test_second_tap_is_acknowledged_without_a_second_day(self, card):
        import asyncio

        from apps.telegram_bot.handlers import ritual_checkin_callback

        for _ in range(2):
            update, q = self._update()
            asyncio.run(ritual_checkin_callback(update, None))
        assert 'уже отмечено' in q.answer.await_args.kwargs['text']
        assert RitualDay.objects.count() == 1

    def test_works_without_any_cards_seeded(self, db):
        """No Card rows (fresh DB) must not crash the tap — the day still counts."""
        import asyncio

        from apps.telegram_bot.handlers import ritual_checkin_callback

        update, q = self._update()
        asyncio.run(ritual_checkin_callback(update, None))
        q.answer.assert_awaited_once()
        q.edit_message_text.assert_not_awaited()
        assert RitualDay.objects.count() == 1
