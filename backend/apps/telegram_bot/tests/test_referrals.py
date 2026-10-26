"""Bring a friend: registration rules, the first-reading payout, caps, and the bot glue."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.telegram_bot import referrals
from apps.telegram_bot.accounts import ensure_user
from apps.telegram_bot.models import Referral, TelegramUser

pytestmark = pytest.mark.django_db


def _tg(tg_id, **kw):
    return TelegramUser.objects.create(tg_id=tg_id, tg_first_name=f'u{tg_id}', locale='ru', **kw)


@pytest.fixture
def inviter(db):
    return _tg(1)


def _first_reading(profile, kind=UsageLedger.KIND_AI_TAROT):
    """What every interpretation view does."""
    return billing.charge_credits(user=ensure_user(profile), kind=kind)


class TestParse:
    @pytest.mark.parametrize('arg,expected', [
        ('ref_123', 123), ('ref_', None), ('ref_abc', None), ('buy_1', None),
        ('contest', None), ('ref_' + '9' * 30, None),
    ])
    def test_parse_ref(self, arg, expected):
        assert referrals.parse_ref(arg) == expected

    def test_link_points_at_the_bot_with_the_ref_argument(self, settings):
        settings.TELEGRAM_BOT_USERNAME = 'my_bot'
        assert referrals.link_for(42) == 'https://t.me/my_bot?start=ref_42'


class TestRegister:
    def test_new_person_via_link_creates_a_pending_referral(self, inviter):
        assert referrals.register(2, 1, first_name='Боря') is True
        ref = Referral.objects.get()
        assert (ref.referrer, ref.invited.tg_id, ref.status) == (inviter, 2, Referral.STATUS_PENDING)

    def test_you_cannot_invite_yourself(self, inviter):
        assert referrals.register(1, 1) is False
        assert Referral.objects.count() == 0

    def test_unknown_inviter_is_ignored(self, db):
        assert referrals.register(2, 999) is False
        assert not TelegramUser.objects.filter(tg_id=2).exists()  # nothing half-created

    def test_someone_already_in_the_bot_is_not_a_referral(self, inviter):
        _tg(2)
        assert referrals.register(2, 1) is False
        assert Referral.objects.count() == 0

    def test_a_second_link_does_not_steal_the_credit(self, inviter):
        _tg(3)
        referrals.register(2, 1)
        assert referrals.register(2, 3) is False   # 2 is no longer new
        assert Referral.objects.get().referrer == inviter

    def test_inviter_at_the_cap_is_not_registered(self, inviter):
        for i in range(referrals.MAX_REWARDED):
            friend = _tg(100 + i)
            Referral.objects.create(referrer=inviter, invited=friend,
                                    status=Referral.STATUS_REWARDED)
        assert referrals.register(2, 1) is False


class TestPayout:
    def _pair(self, inviter):
        referrals.register(2, 1)
        return TelegramUser.objects.get(tg_id=2)

    def test_nothing_is_paid_before_the_first_reading(self, inviter):
        self._pair(inviter)
        assert Referral.objects.get().status == Referral.STATUS_PENDING
        assert billing.credits_balance(ensure_user(inviter)) == 0

    def test_first_reading_pays_both_sides(self, inviter):
        friend = self._pair(inviter)
        _first_reading(friend)
        ref = Referral.objects.get()
        assert ref.status == Referral.STATUS_REWARDED and ref.qualified_at
        assert billing.credits_balance(ensure_user(inviter)) == referrals.REWARD_CREDITS
        assert billing.credits_balance(friend.user) == referrals.REWARD_CREDITS

    def test_it_pays_once_not_per_reading(self, inviter):
        friend = self._pair(inviter)
        for _ in range(3):
            _first_reading(friend)
        assert billing.credits_balance(ensure_user(inviter)) == referrals.REWARD_CREDITS
        assert UsageLedger.objects.filter(kind=UsageLedger.KIND_GRANT_REFERRAL).count() == 2

    @pytest.mark.parametrize('kind', [
        UsageLedger.KIND_AI_RUNES, UsageLedger.KIND_AI_NATAL,
        UsageLedger.KIND_AI_HOROSCOPE,
    ])
    def test_any_kind_of_interpretation_counts(self, inviter, kind):
        friend = self._pair(inviter)
        _first_reading(friend, kind)
        assert Referral.objects.get().status == Referral.STATUS_REWARDED

    def test_receiving_credits_does_not_count_as_a_reading(self, inviter):
        friend = self._pair(inviter)
        billing.grant_credits(ensure_user(friend), 5, UsageLedger.KIND_GRANT_PACK)
        assert Referral.objects.get().status == Referral.STATUS_PENDING

    def test_a_person_nobody_invited_gets_nothing_extra(self, db):
        stranger = _tg(50)
        _first_reading(stranger)
        assert billing.credits_balance(stranger.user) == 0
        assert not UsageLedger.objects.filter(kind=UsageLedger.KIND_GRANT_REFERRAL).exists()

    def test_the_reward_is_spendable(self, inviter):
        """The point of the reward: past the daily allowance the credits are used."""
        friend = self._pair(inviter)
        user = ensure_user(friend)
        for _ in range(billing.FREE_DAILY_LIMIT):
            billing.charge_credits(user=user, kind=UsageLedger.KIND_AI_TAROT)
        charged, balance = billing.charge_credits(user=user, kind=UsageLedger.KIND_AI_TAROT)
        assert charged is True and balance == referrals.REWARD_CREDITS - 1

    def test_inviter_cap_closes_extra_referrals_without_paying(self, inviter):
        for i in range(referrals.MAX_REWARDED):
            Referral.objects.create(referrer=inviter, invited=_tg(100 + i),
                                    status=Referral.STATUS_REWARDED)
        late = _tg(2)
        Referral.objects.create(referrer=inviter, invited=late)  # pending, slipped in earlier
        _first_reading(late)
        assert Referral.objects.get(invited=late).status == Referral.STATUS_CAPPED
        assert billing.credits_balance(ensure_user(late)) == 0
        assert billing.credits_balance(ensure_user(inviter)) == 0

    def test_stats(self, inviter):
        friend = self._pair(inviter)
        referrals.register(3, 1)
        _first_reading(friend)
        assert referrals.stats(inviter) == {
            'rewarded': 1, 'pending': 1, 'credits': 3, 'left': referrals.MAX_REWARDED - 1}

    def test_a_failing_payout_never_breaks_the_reading(self, inviter):
        friend = self._pair(inviter)
        with patch('apps.telegram_bot.referrals.grant_credits', side_effect=RuntimeError('boom')):
            charged, _ = _first_reading(friend)
        assert charged is True


class TestNotify:
    def test_both_people_are_told_after_commit(self, inviter, settings,
                                               django_capture_on_commit_callbacks):
        settings.TELEGRAM_BOT_TOKEN = 't'
        referrals.register(2, 1)
        friend = TelegramUser.objects.get(tg_id=2)
        with patch('apps.telegram_bot.push._send', return_value=True) as send, \
                django_capture_on_commit_callbacks(execute=True):
            _first_reading(friend)
        assert sorted(c.args[1] for c in send.call_args_list) == [1, 2]
        texts = {c.args[1]: c.args[2] for c in send.call_args_list}
        assert 'Приглашено: 1 из' in texts[1]
        assert 'пригласил друг' in texts[2]

    def test_a_telegram_error_is_swallowed(self, inviter, settings):
        settings.TELEGRAM_BOT_TOKEN = 't'
        referrals.register(2, 1)
        ref = Referral.objects.get()
        with patch('apps.telegram_bot.push._send', side_effect=RuntimeError('down')):
            referrals.notify(ref.pk)   # must not raise


def _update(tg_id, lang='ru'):
    user = MagicMock()
    user.id, user.username, user.first_name, user.language_code = tg_id, 'u', 'U', lang
    update = MagicMock()
    update.effective_user = user
    update.message.reply_text = AsyncMock()
    return update


@pytest.mark.django_db(transaction=True)
class TestBotGlue:
    def test_start_with_a_ref_link_registers_before_the_gate(self, inviter):
        from apps.telegram_bot import handlers

        update = _update(2)
        ctx = MagicMock()
        ctx.args, ctx.user_data = ['ref_1'], {}
        with patch.object(handlers, '_start_menu', new=AsyncMock()) as menu:
            asyncio.run(handlers.start(update, ctx))
        menu.assert_awaited_once()                     # the gated menu still runs
        assert Referral.objects.filter(referrer=inviter, invited__tg_id=2).exists()
        assert ctx.user_data['referral_note'] is True

    def test_a_broken_ref_argument_does_not_block_start(self, inviter):
        from apps.telegram_bot import handlers

        update = _update(2)
        ctx = MagicMock()
        ctx.args, ctx.user_data = ['ref_garbage'], {}
        with patch.object(handlers, '_start_menu', new=AsyncMock()) as menu:
            asyncio.run(handlers.start(update, ctx))
        menu.assert_awaited_once()
        assert Referral.objects.count() == 0

    def test_a_plain_start_is_unchanged(self, inviter):
        from apps.telegram_bot import handlers

        update = _update(2)
        ctx = MagicMock()
        ctx.args, ctx.user_data = [], {}
        with patch.object(handlers, '_start_menu', new=AsyncMock()) as menu:
            asyncio.run(handlers.start(update, ctx))
        menu.assert_awaited_once()
        assert 'referral_note' not in ctx.user_data

    def test_invite_command_shows_link_stats_and_share_button(self, inviter, settings):
        from apps.telegram_bot import handlers

        settings.TELEGRAM_BOT_USERNAME = 'my_bot'
        settings.TELEGRAM_REQUIRED_CHANNEL = ''        # gate off
        update = _update(1)
        asyncio.run(handlers.invite_command(update, MagicMock(user_data={})))
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.await_args.args[0]
        kwargs = update.message.reply_text.await_args.kwargs
        assert 'https://t.me/my_bot?start=ref_1' in text
        assert 'Приглашено: 0 из 5' in text
        button = kwargs['reply_markup'].inline_keyboard[0][0]
        assert button.url.startswith('https://t.me/share/url?url=')
        assert 'ref_1' in button.url or 'ref_1' in button.url.replace('%3D', '=')
