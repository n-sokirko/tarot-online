"""Tests for the channel autoposter: dedup logic and the two routine endpoints."""
from unittest.mock import patch

import pytest
from django.test import Client, override_settings

from apps.telegram_bot import channel
from apps.telegram_bot.models import ChannelPost

BRIEF = "/api/v1/channel/brief/"
PUBLISH = "/api/v1/channel/publish/"
TOKEN = "test-channel-token"

TOWER = (
    "<b>Башня — это не катастрофа, а освобождение.</b>\n\n"
    "XVI аркан рушит фундамент, на котором стоять было нельзя. "
    "Больно, но после неё дышится свободнее.\n\n"
    "Разбери свою ситуацию → @tarott_online_bot"
)
# Same claim, different wording — this is exactly the case a topic-only ban list
# misses and the fingerprint/similarity check has to catch.
TOWER_REWORDED = (
    "<b>Башня рушит то, на чём нельзя было стоять.</b>\n\n"
    "Шестнадцатый аркан ломает ложный фундамент. Это больно, "
    "зато дышится потом свободнее.\n\n"
    "Разбери ситуацию → @tarott_online_bot"
)
RUNES = (
    "<b>Футарк назван по своим первым буквам.</b>\n\n"
    "F-U-Th-A-R-K — германские племена пользовались этим алфавитом "
    "примерно с 150 по 800 год.\n\n"
    "Спроси руны → @tarott_online_bot"
)


class TestSimilarity:
    def test_identical_text_is_fully_similar(self):
        assert channel.similarity(TOWER, TOWER) == pytest.approx(1.0)

    def test_reworded_duplicate_trips_the_limit(self):
        assert channel.similarity(TOWER, TOWER_REWORDED) >= channel.SIMILARITY_LIMIT

    def test_different_topics_stay_below_the_limit(self):
        """Two genuinely different posts must not collide — otherwise the
        generator would keep rejecting perfectly good posts."""
        assert channel.similarity(TOWER, RUNES) < channel.SIMILARITY_LIMIT

    def test_fingerprint_ignores_markup_and_case(self):
        assert channel.fingerprint(TOWER) == channel.fingerprint(TOWER.upper().replace("<B>", "<b>"))

    def test_fingerprint_differs_across_posts(self):
        assert channel.fingerprint(TOWER) != channel.fingerprint(RUNES)


@pytest.mark.django_db
class TestNextKind:
    def test_rotation_is_two_facts_then_a_promo(self):
        kinds = []
        for _ in range(6):
            kinds.append(channel.next_kind())
            ChannelPost.objects.create(
                kind=kinds[-1], topic=f"t{len(kinds)}", text=f"text {len(kinds)}",
                fingerprint=f"fp{len(kinds)}", status=ChannelPost.STATUS_PUBLISHED,
            )
        assert kinds == ["fact", "fact", "promo", "fact", "fact", "promo"]

    def test_unpublished_rows_do_not_shift_the_rotation(self):
        """A failed send must not push the ratio out of phase."""
        ChannelPost.objects.create(kind="fact", topic="t", text="x", fingerprint="f",
                                   status=ChannelPost.STATUS_FAILED)
        assert channel.next_kind() == "fact"


@pytest.mark.django_db
class TestBriefEndpoint:
    @override_settings(CHANNEL_POST_TOKEN="")
    def test_refuses_when_token_not_configured(self):
        resp = Client().get(BRIEF, headers={"x-channel-token": "anything"})
        assert resp.status_code == 403

    @override_settings(CHANNEL_POST_TOKEN=TOKEN)
    def test_refuses_wrong_token(self):
        assert Client().get(BRIEF, headers={"x-channel-token": "nope"}).status_code == 403

    @override_settings(CHANNEL_POST_TOKEN=TOKEN)
    def test_returns_used_topics(self):
        ChannelPost.objects.create(kind="fact", topic="Башня", text=TOWER,
                                   fingerprint=channel.fingerprint(TOWER),
                                   status=ChannelPost.STATUS_PUBLISHED)
        resp = Client().get(BRIEF, headers={"x-channel-token": TOKEN})
        assert resp.status_code == 200
        body = resp.json()
        assert "Башня" in body["used_topics"]
        assert body["published_total"] == 1
        assert body["kind"] in ("fact", "promo")


@pytest.mark.django_db
class TestPublishEndpoint:
    @pytest.fixture(autouse=True)
    def _token(self, settings):
        # override_settings cannot decorate a plain pytest class, so the token is
        # set through pytest-django's settings fixture instead.
        settings.CHANNEL_POST_TOKEN = TOKEN

    def _post(self, payload):
        return Client().post(PUBLISH, payload, content_type="application/json",
                             headers={"x-channel-token": TOKEN})

    def test_requires_topic_and_text(self):
        assert self._post({"topic": "", "text": ""}).status_code == 400

    def test_rejects_unknown_kind(self):
        assert self._post({"topic": "t", "text": TOWER, "kind": "spam"}).status_code == 400

    def test_publishes_and_records(self):
        with patch("apps.telegram_bot.channel.send_to_channel", return_value=4242) as send:
            resp = self._post({"topic": "Башня", "text": TOWER, "kind": "fact"})
        assert resp.status_code == 201
        assert resp.json()["message_id"] == 4242
        send.assert_called_once_with(TOWER)
        row = ChannelPost.objects.get()
        assert row.status == ChannelPost.STATUS_PUBLISHED
        assert row.tg_message_id == 4242
        assert row.fingerprint == channel.fingerprint(TOWER)

    def test_rejects_a_reworded_repeat(self):
        ChannelPost.objects.create(kind="fact", topic="Башня", text=TOWER,
                                   fingerprint=channel.fingerprint(TOWER),
                                   status=ChannelPost.STATUS_PUBLISHED)
        with patch("apps.telegram_bot.channel.send_to_channel") as send:
            resp = self._post({"topic": "Шестнадцатый аркан", "text": TOWER_REWORDED})
        assert resp.status_code == 409
        assert resp.json()["conflicts_with"] == "Башня"
        send.assert_not_called()
        assert ChannelPost.objects.count() == 1

    def test_allows_a_genuinely_new_post(self):
        ChannelPost.objects.create(kind="fact", topic="Башня", text=TOWER,
                                   fingerprint=channel.fingerprint(TOWER),
                                   status=ChannelPost.STATUS_PUBLISHED)
        with patch("apps.telegram_bot.channel.send_to_channel", return_value=1):
            resp = self._post({"topic": "Футарк", "text": RUNES})
        assert resp.status_code == 201
        assert ChannelPost.objects.count() == 2

    def test_send_failure_is_recorded_not_swallowed(self):
        """A post that never reached Telegram must be visible as failed — and it
        must not be counted as published, or the fact/promo ratio drifts."""
        with patch("apps.telegram_bot.channel.send_to_channel",
                   side_effect=RuntimeError("telegram down")):
            resp = self._post({"topic": "Башня", "text": TOWER})
        assert resp.status_code == 502
        row = ChannelPost.objects.get()
        assert row.status == ChannelPost.STATUS_FAILED
        assert "telegram down" in row.error
