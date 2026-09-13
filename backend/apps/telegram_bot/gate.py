"""Channel-subscription gate.

Wraps bot handlers so they only run if the user is a member of
TELEGRAM_REQUIRED_CHANNEL. If not, the user is shown a message with a "Subscribe"
link and a "I subscribed" button that re-checks. The membership check is cached
in user_data for CHECK_TTL seconds to keep API traffic low.

Bot must be an admin in the channel for getChatMember to return membership info.
If TELEGRAM_REQUIRED_CHANNEL is empty, the gate is a no-op.
"""
import functools
import logging
import time

from django.conf import settings
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)

CHECK_TTL = 300  # seconds — re-check membership every 5 minutes per user
_MEMBER_STATUSES = {"member", "administrator", "creator", "restricted"}
# "left" and "kicked" are explicitly not members.


async def _is_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool | None:
    """Returns True/False, or None if the check itself failed (treat as 'allow'
    to fail open: a misconfigured channel shouldn't lock everyone out)."""
    channel = getattr(settings, "TELEGRAM_REQUIRED_CHANNEL", "")
    if not channel:
        return True
    try:
        cm = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
    except (BadRequest, Forbidden) as e:
        # Most common cause: bot is not an admin in the channel. Log loudly so
        # we notice misconfiguration; fail open to avoid soft-locking the bot.
        log.warning("Channel-gate check failed for channel %s user %s: %s",
                    channel, user_id, e)
        return None
    return cm.status in _MEMBER_STATUSES


def _gate_keyboard(locale: str) -> InlineKeyboardMarkup:
    url = getattr(settings, "TELEGRAM_REQUIRED_CHANNEL_URL", "https://t.me/tarro_bot_group")
    if locale == "ru":
        subscribe = "📣 Подписаться на канал"
        check = "✅ Я подписался"
    else:
        subscribe = "📣 Subscribe to channel"
        check = "✅ I subscribed"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(subscribe, url=url)],
        [InlineKeyboardButton(check, callback_data="gate:check")],
    ])


def _gate_text(locale: str) -> str:
    if locale == "ru":
        return (
            "🔒 *Чтобы пользоваться ботом, подпишись на канал.*\n\n"
            "Там — карта дня, факты про Таро и анонсы. После подписки нажми "
            "«Я подписался» — и сразу продолжим."
        )
    return (
        "🔒 *To use the bot, please subscribe to our channel.*\n\n"
        "It's where the card of the day, tarot facts and updates live. "
        "After subscribing, tap 'I subscribed' and we'll continue."
    )


async def _send_gate(update: Update, locale: str) -> None:
    text = _gate_text(locale)
    markup = _gate_keyboard(locale)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=markup,
        )
        return
    await update.effective_message.reply_text(
        text, parse_mode="Markdown", reply_markup=markup,
    )


async def _check_cached(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool | None:
    """Cached wrapper around _is_member. The 'allowed' result is cached for
    CHECK_TTL; a denial is NOT cached, so the user retries quickly after
    subscribing."""
    ud = context.user_data if context.user_data is not None else {}
    cached_until = ud.get("gate_ok_until", 0)
    if cached_until > time.time():
        return True
    ok = await _is_member(context, user_id)
    if ok is True and context.user_data is not None:
        context.user_data["gate_ok_until"] = time.time() + CHECK_TTL
    return ok


def requires_channel_sub(handler):
    """Decorator: only run the wrapped handler if the user is subscribed.

    Use a lightweight wrapper that short-circuits to the gate message on a 'no'.
    On a check failure (None) we fail OPEN so misconfiguration doesn't brick the bot.
    """
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        tg = update.effective_user
        if tg is None:
            return await handler(update, context)
        ok = await _check_cached(context, tg.id)
        if ok is False:
            # Lazy import to avoid a circular: handlers.py uses _norm_locale only.
            from apps.telegram_bot.handlers import _norm_locale
            await _send_gate(update, _norm_locale(tg.language_code))
            return
        return await handler(update, context)
    return wrapper


async def gate_recheck_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the 'I subscribed' button. Re-checks (no cache), and either
    welcomes the user in or repeats the gate message."""
    from apps.telegram_bot.handlers import _norm_locale  # local import — circular

    q: CallbackQuery = update.callback_query
    tg = update.effective_user
    locale = _norm_locale(tg.language_code if tg else None)
    # Force a fresh check (clear the cache, then call cached helper).
    if context.user_data is not None:
        context.user_data.pop("gate_ok_until", None)
    ok = await _check_cached(context, tg.id)
    if ok:
        await q.answer("✅" if locale != "ru" else "✅ Готово")
        msg = ("Спасибо! Доступ открыт. Напиши /start, чтобы продолжить."
               if locale == "ru" else
               "Thanks! You're in. Send /start to continue.")
        await q.edit_message_text(msg)
        return
    await q.answer(
        "Пока не вижу подписки. Попробуй ещё раз через минуту." if locale == "ru"
        else "I don't see the subscription yet. Try again in a moment.",
        show_alert=True,
    )
