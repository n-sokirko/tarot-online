"""Telegram Application factory — shared by polling (dev) and webhook (prod)."""
import logging

from django.conf import settings
from telegram import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    MenuButtonWebApp,
    WebAppInfo,
)
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

log = logging.getLogger(__name__)


async def _post_init(app: Application) -> None:
    """
    Runs once after the bot is initialised but before polling/webhook starts.

    Registers:
      • The slash-command menu (so users see /start, /status in the bot UI).
      • The persistent menu button next to the message input — opens the
        Mini App with one tap, every time the user lands in the chat.
    """
    webapp_url = getattr(settings, 'WEBAPP_URL', 'https://sokirdon.com')

    try:
        await app.bot.set_my_commands(
            commands=[
                BotCommand('start', '🌙 Открыть меню'),
                BotCommand('birthday', '🎂 Дата рождения · гороскоп'),
                BotCommand('contest', '🎁 Конкурс — выиграй Premium'),
                BotCommand('status', '⭐ Моя подписка'),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )
        log.info('Bot commands registered')
    except Exception:
        log.exception('set_my_commands failed')

    try:
        await app.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text='Открыть приложение',
                web_app=WebAppInfo(url=webapp_url),
            ),
        )
        log.info('Chat menu button → WebApp set to %s', webapp_url)
    except Exception:
        log.exception('set_chat_menu_button failed')


def create_application() -> Application:
    # Generous timeouts so transient network blips don't kill the bot.
    # Default httpx timeouts (5s) are too aggressive for unreliable links.
    builder = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(40.0)
        .post_init(_post_init)
    )
    app = builder.build()

    from apps.telegram_bot.handlers import (
        birthday_command,
        handle_text,
        pre_checkout_query,
        start,
        status_command,
        subscribe,
        successful_payment,
        unsubscribe,
    )

    from apps.telegram_bot.gate import gate_recheck_callback
    from apps.contest.handlers import (
        contest_command, contest_top_command, contest_top_callback, on_chat_member,
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('subscribe', subscribe))
    app.add_handler(CommandHandler('unsubscribe', unsubscribe))
    app.add_handler(CommandHandler('birthday', birthday_command))
    app.add_handler(CommandHandler('contest', contest_command))
    app.add_handler(CommandHandler('contest_top', contest_top_command))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_query))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    # "I subscribed" recheck button on the channel-subscription gate.
    app.add_handler(CallbackQueryHandler(gate_recheck_callback, pattern=r'^gate:check$'))
    app.add_handler(CallbackQueryHandler(contest_top_callback, pattern=r'^contest:top$'))
    # Channel member updates — tally contest invites.
    app.add_handler(ChatMemberHandler(on_chat_member, ChatMemberHandler.CHAT_MEMBER))
    # Plain text — only reacts while awaiting a birth date (see handle_text).
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


# The polling loop needs to subscribe to chat_member updates explicitly — they're
# off by default. Used by run_bot.py.
BOT_ALLOWED_UPDATES = [
    Update.MESSAGE, Update.CALLBACK_QUERY, Update.PRE_CHECKOUT_QUERY,
    Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER,
]
