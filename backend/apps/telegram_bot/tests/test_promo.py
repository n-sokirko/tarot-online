"""Warm-up campaign: a video sent to the bot pays out free readings exactly once."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.billing.models import CreditWallet, UsageLedger
from apps.telegram_bot import promo
from apps.telegram_bot.models import TelegramUser

pytestmark = pytest.mark.django_db


def _balance(tg_id):
    user = TelegramUser.objects.get(tg_id=tg_id).user
    return CreditWallet.objects.get(user=user).balance


class TestClaim:
    def test_first_video_grants_the_bonus_to_a_new_person(self):
        assert promo.claim_video_bonus(10, first_name='Аня') is True
        assert _balance(10) == 3
        row = UsageLedger.objects.get(kind=UsageLedger.KIND_GRANT_PROMO)
        assert (row.cost_credits, row.reference_id) == (-3, promo.REFERENCE)

    def test_second_video_pays_nothing(self):
        promo.claim_video_bonus(10)
        assert promo.claim_video_bonus(10) is False
        assert _balance(10) == 3
        assert UsageLedger.objects.filter(kind=UsageLedger.KIND_GRANT_PROMO).count() == 1

    def test_existing_profile_keeps_its_data_and_gets_the_bonus(self):
        TelegramUser.objects.create(tg_id=11, tg_first_name='Боря', locale='en')
        assert promo.claim_video_bonus(11, first_name='Другое имя') is True
        assert TelegramUser.objects.get(tg_id=11).tg_first_name == 'Боря'

    def test_amount_comes_from_settings(self, settings):
        settings.PROMO_VIDEO_CREDITS = 5
        promo.claim_video_bonus(12)
        assert _balance(12) == 5


@pytest.mark.django_db(transaction=True)  # sync_to_async runs on another thread/connection
class TestHandler:
    def _update(self, tg_id=20):
        upd = MagicMock()
        upd.effective_user.id = tg_id
        upd.effective_user.username = 'u'
        upd.effective_user.first_name = 'U'
        upd.effective_user.language_code = 'ru'
        upd.message.reply_text = AsyncMock()
        return upd

    def _run(self, upd):
        from apps.telegram_bot import handlers
        with patch('apps.telegram_bot.gate._check_cached', AsyncMock(return_value=True)):
            asyncio.run(handlers.promo_video(upd, MagicMock()))

    def test_replies_with_the_gift_and_a_button(self):
        upd = self._update()
        self._run(upd)
        text = upd.message.reply_text.call_args.args[0]
        assert '3 бесплатных расклада' in text
        assert _balance(20) == 3

    def test_repeat_explains_it_is_one_per_person(self):
        upd = self._update()
        self._run(upd)
        self._run(upd)
        assert 'один раз' in upd.message.reply_text.call_args.args[0]
        assert _balance(20) == 3

    def test_disabled_campaign_ignores_videos(self, settings):
        settings.PROMO_VIDEO_ENABLED = False
        upd = self._update()
        self._run(upd)
        upd.message.reply_text.assert_not_called()
        assert not TelegramUser.objects.filter(tg_id=20).exists()
