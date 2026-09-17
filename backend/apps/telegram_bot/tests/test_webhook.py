"""Tests for the Telegram webhook entry point and the sync->async bridge."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from apps.telegram_bot.bot_runtime import _process_update

WEBHOOK_URL = "/api/v1/telegram/webhook/"
UPDATE = {"update_id": 1, "message": {"message_id": 1, "text": "/start"}}


@pytest.mark.django_db
class TestTelegramWebhookView:
    def test_url_is_wired(self):
        assert reverse("telegram-webhook") == WEBHOOK_URL

    @override_settings(TELEGRAM_WEBHOOK_SECRET="")
    def test_refuses_when_no_secret_configured(self):
        """Fail closed: an unset secret must not mean "accept anything"."""
        with patch("apps.telegram_bot.bot_runtime.process_update_sync") as process:
            resp = Client().post(
                WEBHOOK_URL, UPDATE, content_type="application/json",
                headers={"x-telegram-bot-api-secret-token": "anything"},
            )
        assert resp.status_code == 403
        process.assert_not_called()

    @override_settings(TELEGRAM_WEBHOOK_SECRET="s3cret")
    def test_refuses_wrong_secret(self):
        with patch("apps.telegram_bot.bot_runtime.process_update_sync") as process:
            resp = Client().post(
                WEBHOOK_URL, UPDATE, content_type="application/json",
                headers={"x-telegram-bot-api-secret-token": "wrong"},
            )
        assert resp.status_code == 403
        process.assert_not_called()

    @override_settings(TELEGRAM_WEBHOOK_SECRET="s3cret")
    def test_refuses_missing_header(self):
        with patch("apps.telegram_bot.bot_runtime.process_update_sync") as process:
            resp = Client().post(WEBHOOK_URL, UPDATE, content_type="application/json")
        assert resp.status_code == 403
        process.assert_not_called()

    @override_settings(TELEGRAM_WEBHOOK_SECRET="s3cret")
    def test_processes_update_with_correct_secret(self):
        with patch("apps.telegram_bot.bot_runtime.process_update_sync") as process:
            resp = Client().post(
                WEBHOOK_URL, UPDATE, content_type="application/json",
                headers={"x-telegram-bot-api-secret-token": "s3cret"},
            )
        assert resp.status_code == 200
        process.assert_called_once_with(UPDATE)

    @override_settings(TELEGRAM_WEBHOOK_SECRET="s3cret")
    def test_answers_200_even_when_handler_blows_up(self):
        """Telegram backs off and eventually suspends delivery on repeated
        non-2xx answers, so a broken handler must not become a broken bot."""
        with patch(
            "apps.telegram_bot.bot_runtime.process_update_sync",
            side_effect=RuntimeError("boom"),
        ):
            resp = Client().post(
                WEBHOOK_URL, UPDATE, content_type="application/json",
                headers={"x-telegram-bot-api-secret-token": "s3cret"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}


class ProcessUpdateConnectionRefreshTests(SimpleTestCase):
    """Regression guard for the stale-Postgres-connection bug that took Liana
    Studio's bot down silently on 2026-08-24. The bridge runs handlers via
    sync_to_async outside any AsyncToSync context, so asgiref executes them on
    one background thread that lives for the whole process. Django refreshes
    stale connections only on request_started/request_finished — signals that
    thread never receives — so its first DB connection is never health-checked
    again, and every update after Postgres drops it for being idle fails with
    "the connection is closed" while the webhook still answers 200 (the bot
    looks dead silent). _process_update must call close_old_connections()
    BEFORE any handler touches the DB."""

    def test_refreshes_db_connections_before_processing_update(self):
        calls = []
        application = AsyncMock()
        application.process_update.side_effect = lambda *_: calls.append("process_update")

        with patch(
            "django.db.close_old_connections",
            side_effect=lambda: calls.append("close_old_connections"),
        ):
            asyncio.run(_process_update(application, object()))

        # Order matters: the refresh must happen before process_update touches
        # the DB, not merely "at some point" during the call.
        assert calls == ["close_old_connections", "process_update"]
