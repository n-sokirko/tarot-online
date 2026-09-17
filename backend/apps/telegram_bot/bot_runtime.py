"""
Bridge between the synchronous Django/gunicorn worker and the asynchronous
python-telegram-bot Application, so updates can be handled through a webhook
(TelegramWebhookView) instead of run_polling() in a separate always-on process.

PTB's Application owns an httpx.AsyncClient bound to the event loop it was
initialised in — spinning up a fresh loop per request (asyncio.run() per
update) breaks that client on the second request. So this module keeps ONE
long-lived event loop on a background thread for the whole worker process:
the Application is initialised there once, and every incoming update is just
scheduled onto that same loop via run_coroutine_threadsafe.
"""
import asyncio
import logging
import threading

logger = logging.getLogger(__name__)

_loop: asyncio.AbstractEventLoop | None = None
_application = None
_init_lock = threading.Lock()


def _run_loop_forever(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_application():
    """Lazily create the background event loop + an initialised Application —
    exactly once per worker process. Thread-safe."""
    global _loop, _application

    if _application is not None:
        return _application, _loop

    with _init_lock:
        if _application is not None:
            return _application, _loop

        from django.conf import settings

        from apps.telegram_bot.bot import create_application

        if not settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError(
                'TELEGRAM_BOT_TOKEN is not set — cannot process webhook updates.'
            )

        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=_run_loop_forever, args=(loop,), daemon=True)
        thread.start()

        application = create_application()
        asyncio.run_coroutine_threadsafe(application.initialize(), loop).result(timeout=15)
        # Application.initialize() deliberately does NOT call post_init (only
        # run_polling()/run_webhook() do, per its docstring) — this bridge drives
        # initialize() directly, so it must invoke the hook itself, otherwise the
        # "/" command menu and the WebApp menu button are never registered.
        if application.post_init is not None:
            asyncio.run_coroutine_threadsafe(
                application.post_init(application), loop
            ).result(timeout=15)

        _loop = loop
        _application = application
        logger.info('Telegram bot Application initialized for webhook processing.')
        return _application, _loop


async def _process_update(application, update) -> None:
    # Outside of an AsyncToSync context (which this manually-driven event loop
    # never creates), asgiref runs every thread_sensitive sync_to_async call —
    # i.e. all DB access inside the bot's handlers — on ONE persistent
    # background thread it keeps for the process's whole lifetime. Django only
    # refreshes/closes stale connections in close_old_connections(), which fires
    # on request_started/request_finished — signals that thread never receives.
    # So the first connection it ever opens is never health-checked again; once
    # Postgres (or Railway's proxy) drops it for being idle, every later webhook
    # update dies with "the connection is closed" — silently, because the view
    # always answers 200. Scheduling this first, on the same executor thread,
    # refreshes the connection registry before any handler touches the DB.
    # (Same bug bit Liana Studio in production on 2026-08-24.)
    from asgiref.sync import sync_to_async
    from django.db import close_old_connections

    await sync_to_async(close_old_connections, thread_sensitive=True)()
    await application.process_update(update)


def process_update_sync(update_payload: dict, timeout: float = 25.0) -> None:
    """Feed the bot one update (already-parsed JSON from the webhook body),
    blocking until it has been handled. Call from a sync Django view."""
    from telegram import Update

    application, loop = get_application()
    update = Update.de_json(update_payload, application.bot)
    asyncio.run_coroutine_threadsafe(
        _process_update(application, update), loop
    ).result(timeout=timeout)
