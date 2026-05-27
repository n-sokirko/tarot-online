"""Telegram Application factory — shared by polling (dev) and webhook (prod)."""
import logging

from django.conf import settings
from telegram import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    MenuButtonWebApp,
    WebAppInfo,
)
from telegram.ext import (
    Application,
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
        pre_checkout_query,
        start,
        status_command,
        successful_payment,
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_query))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    return app
