"""Telegram bot handlers: /start, /status, /birthday, invoice flow, successful_payment."""
import datetime
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update, WebAppInfo
from telegram.ext import ContextTypes

from apps.telegram_bot.birth import natal_birth_date as _natal_birth_date
from apps.telegram_bot.dates import parse_birth_date as _parse_birth_date
from apps.telegram_bot.gate import requires_channel_sub
from apps.telegram_bot.tokens import validate_payment_token

log = logging.getLogger(__name__)

# ── DB helpers (sync → async wrappers) ────────────────────────────────────────

@sync_to_async
def _get_plan(slug: str):
    from apps.billing.models import Plan
    return Plan.objects.get(slug=slug, is_active=True, tg_stars_price__gt=0)


def _norm_locale(language_code: str | None) -> str:
    """Card content exists in ru/en only — normalise a Telegram language code."""
    return 'ru' if str(language_code or '').startswith('ru') else 'en'


@sync_to_async
def _store_user_locale(tg_id: int, username: str, first_name: str, locale: str) -> bool:
    """Upsert a TelegramUser with their language so daily pushes match it.

    Called from /start — the main funnel for marketing traffic — so even before a
    user opens the Mini App we know which language to send their card-of-the-day in.
    Preserves the daily_push opt-in if the row already exists.
    Returns True if the user's birth date is already known (for the /start hint).
    """
    from apps.telegram_bot.models import TelegramUser
    obj, _ = TelegramUser.objects.update_or_create(
        tg_id=tg_id,
        defaults={'tg_username': username, 'tg_first_name': first_name, 'locale': locale},
    )
    return obj.birth_date is not None


@sync_to_async
def _get_birth_date(tg_id: int) -> datetime.date | None:
    """Known birth date — from the stored field, else the user's natal chart
    (cached back onto the row), else None."""
    from apps.telegram_bot.models import TelegramUser
    try:
        u = TelegramUser.objects.select_related('user').get(tg_id=tg_id)
    except TelegramUser.DoesNotExist:
        return None
    if u.birth_date:
        return u.birth_date
    bd = _natal_birth_date(u)
    if bd:
        u.birth_date = bd
        u.save(update_fields=['birth_date'])
    return bd


@sync_to_async
def _save_birth_date(tg_id: int, birth_date: datetime.date, username: str = '',
                     first_name: str = '', locale: str = 'ru') -> None:
    """Store the birth date and opt the user into the morning push (setting a
    birthday is strong intent for the personal horoscope; disclosed in the reply)."""
    from apps.telegram_bot.models import TelegramUser
    obj, _ = TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={'tg_username': username, 'tg_first_name': first_name, 'locale': locale},
    )
    obj.birth_date = birth_date
    obj.daily_push = True
    obj.locale = locale
    obj.save(update_fields=['birth_date', 'daily_push', 'locale'])


@sync_to_async
def _link_tg_user(tg_id: int, tg_username: str, tg_first_name: str, user_id: int | None,
                  locale: str = 'ru'):
    from apps.telegram_bot.models import TelegramUser
    defaults = {'tg_username': tg_username, 'tg_first_name': tg_first_name, 'locale': locale}
    if user_id is not None:
        from django.contrib.auth import get_user_model
        try:
            defaults['user'] = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            pass
    obj, _ = TelegramUser.objects.update_or_create(tg_id=tg_id, defaults=defaults)
    return obj


@sync_to_async
def _activate(user_id: int, plan_slug: str, charge_id: str) -> str:
    from django.contrib.auth import get_user_model
    from apps.billing.models import Plan
    from apps.billing import services as billing_services

    User = get_user_model()
    user = User.objects.get(pk=user_id)
    plan = Plan.objects.get(slug=plan_slug)
    billing_services.apply_tg_payment(user=user, plan=plan, charge_id=charge_id)
    return plan.name_ru


@sync_to_async
def _get_status(tg_id: int) -> str:
    from apps.telegram_bot.models import TelegramUser
    from apps.billing import services as billing_services

    try:
        profile = TelegramUser.objects.select_related('user').get(tg_id=tg_id)
    except TelegramUser.DoesNotExist:
        return 'not_linked'
    if not profile.user:
        return 'not_linked'
    info = billing_services.tier_for(profile.user)
    credits = billing_services.credits_balance(profile.user)
    return f'tier:{info.tier},credits:{credits}'


@sync_to_async
def _set_daily_push(tg_id: int, on: bool, username: str = '', first_name: str = '',
                    locale: str = 'ru') -> None:
    from apps.telegram_bot.models import TelegramUser
    obj, _ = TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={'tg_username': username, 'tg_first_name': first_name, 'locale': locale},
    )
    obj.daily_push = on
    obj.locale = locale
    obj.save(update_fields=['daily_push', 'locale'])


# ── Handlers ───────────────────────────────────────────────────────────────────


@requires_channel_sub
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    locale = _norm_locale(tg.language_code)
    await _set_daily_push(tg.id, True, tg.username or '', tg.first_name or '', locale)
    if locale == 'ru':
        msg = ("🌙 Готово! Каждое утро буду присылать твою карту дня.\n"
               "Чтобы отписаться — /unsubscribe")
    else:
        msg = ("🌙 Done! I'll send your card of the day every morning.\n"
               "To stop — /unsubscribe")
    await update.message.reply_text(msg)


@requires_channel_sub
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    locale = _norm_locale(tg.language_code)
    await _set_daily_push(tg.id, False, tg.username or '', tg.first_name or '', locale)
    msg = ("Отписал от ежедневных карт 🌙 Вернуться — /subscribe" if locale == 'ru'
           else "Unsubscribed from daily cards 🌙 Come back — /subscribe")
    await update.message.reply_text(msg)

@requires_channel_sub
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if args and args[0].startswith('buy_'):
        await _handle_buy(update, context, args[0][4:])
        return
    if args and args[0].startswith('donate_'):
        await _handle_donate(update, context, args[0][7:])
        return
    if args and args[0] == 'contest':
        # Deep-link from the channel post's «Участвовать» button.
        from apps.contest.handlers import contest_join
        await contest_join(update, context)
        return

    tg = update.effective_user
    locale = _norm_locale(tg.language_code if tg else None)
    has_birth = False
    if tg:
        has_birth = await _store_user_locale(tg.id, tg.username or '', tg.first_name or '', locale)

    webapp_url = getattr(settings, 'WEBAPP_URL', 'https://sokirdon.com')

    if locale == 'ru':
        btn = "🌙 Открыть расклады"
        text = (
            "🌙 *Tarot Online Bot*\n\n"
            "Нажми кнопку ниже, чтобы открыть расклады прямо в Telegram — "
            "без регистрации, всё сохраняется в аккаунт автоматически.\n\n"
            "Здесь также можно оплатить Premium-подписку через Telegram Stars ⭐\n\n"
            "/status — проверить подписку"
        )
    else:
        btn = "🌙 Open readings"
        text = (
            "🌙 *Tarot Online Bot*\n\n"
            "Tap the button below to open readings right inside Telegram — "
            "no signup, everything saves to your account automatically.\n\n"
            "You can also get Premium via Telegram Stars ⭐\n\n"
            "/status — check your subscription"
        )

    if not has_birth:
        text += (
            "\n\n🎂 /birthday — добавь дату рождения, и я буду присылать твой "
            "персональный гороскоп каждое утро."
            if locale == 'ru' else
            "\n\n🎂 /birthday — add your birth date for a personal daily horoscope."
        )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(btn, web_app=WebAppInfo(url=webapp_url)),
    ]])

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=keyboard,
    )


def _sign_label(birth_date: datetime.date, locale: str) -> str:
    """Human label like '♋ Рак' / '♋ Cancer' for a birth date."""
    from apps.horoscope.services import sign_for_date
    s = sign_for_date(birth_date.month, birth_date.day)
    if not s:
        return ''
    return f"{s['symbol']} {s['name_ru'] if locale == 'ru' else s['name_en']}"


@requires_channel_sub
async def birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask for (or offer to change) the user's birth date for the daily horoscope."""
    tg = update.effective_user
    locale = _norm_locale(tg.language_code)
    bd = await _get_birth_date(tg.id)
    if context.user_data is not None:
        context.user_data['awaiting_birthday'] = True
    if bd:
        label = _sign_label(bd, locale)
        if locale == 'ru':
            msg = (f"Сейчас записана дата: *{bd.strftime('%d.%m.%Y')}* ({label}).\n"
                   "Хочешь изменить — просто пришли новую дату в формате ДД.ММ.ГГГГ.")
        else:
            msg = (f"Saved birth date: *{bd.strftime('%d.%m.%Y')}* ({label}).\n"
                   "To change it, just send a new date as DD.MM.YYYY.")
    else:
        if locale == 'ru':
            msg = ("🎂 Пришли свою дату рождения в формате *ДД.ММ.ГГГГ* (например, 14.03.1995) — "
                   "и каждое утро я буду присылать тебе персональный гороскоп по твоему знаку.")
        else:
            msg = ("🎂 Send your birth date as *DD.MM.YYYY* (e.g. 14.03.1995) — "
                   "and every morning I'll send you a personal horoscope for your sign.")
    await update.message.reply_text(msg, parse_mode='Markdown')


@requires_channel_sub
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plain-text handler — only acts while we're waiting for a birth date."""
    if not (context.user_data or {}).get('awaiting_birthday'):
        return
    tg = update.effective_user
    locale = _norm_locale(tg.language_code)
    bd = _parse_birth_date(update.message.text)
    if not bd:
        msg = ("Не понял дату 🙈 Пришли в формате ДД.ММ.ГГГГ, например 14.03.1995."
               if locale == 'ru' else
               "I couldn't read that date 🙈 Please use DD.MM.YYYY, e.g. 14.03.1995.")
        await update.message.reply_text(msg)
        return

    if context.user_data is not None:
        context.user_data['awaiting_birthday'] = False
    await _save_birth_date(tg.id, bd, tg.username or '', tg.first_name or '', locale)
    label = _sign_label(bd, locale)
    webapp = getattr(settings, 'WEBAPP_URL', 'https://sokirdon.com')
    if locale == 'ru':
        text = (f"Готово! Твой знак — *{label}* ✨\n\n"
                "Каждое утро буду присылать персональный гороскоп. Выключить — /unsubscribe.")
        btn = "🔮 Открыть гороскоп"
    else:
        text = (f"Done! Your sign is *{label}* ✨\n\n"
                "I'll send you a personal horoscope every morning. To stop — /unsubscribe.")
        btn = "🔮 Open horoscope"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(btn, web_app=WebAppInfo(url=f"{webapp}/horoscope")),
    ]])
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)


@requires_channel_sub
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    raw = await _get_status(tg.id)
    if raw == 'not_linked':
        await update.message.reply_text(
            "Аккаунт не привязан. Перейди на сайт и нажми «Оплатить через Telegram»."
        )
        return
    parts = dict(p.split(':') for p in raw.split(','))
    tier = parts.get('tier', 'free')
    credits = parts.get('credits', '0')
    emoji = '⭐' if tier == 'premium' else '🆓'
    await update.message.reply_text(
        f"{emoji} *Тариф:* {tier.capitalize()}\n"
        f"💎 *Кредиты:* {credits}",
        parse_mode='Markdown',
    )


async def _handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    payload = validate_payment_token(token)
    if not payload:
        await update.message.reply_text(
            "❌ Ссылка недействительна или устарела.\n"
            "Вернись на сайт и нажми кнопку снова."
        )
        return

    user_id: int = payload['user_id']
    plan_slug: str = payload['plan_slug']

    try:
        plan = await _get_plan(plan_slug)
    except Exception:
        await update.message.reply_text("❌ Тариф не найден. Обратись в поддержку.")
        return

    tg = update.effective_user
    await _link_tg_user(tg.id, tg.username or '', tg.first_name or '', user_id,
                        _norm_locale(tg.language_code))

    # Store for pre_checkout / successful_payment
    context.chat_data['pending'] = {'user_id': user_id, 'plan_slug': plan_slug}

    await update.message.reply_invoice(
        title=plan.name_ru,
        description=plan.description_ru[:255],
        payload=f'buy|{plan_slug}|{user_id}',
        currency='XTR',
        prices=[LabeledPrice(plan.name_ru, plan.tg_stars_price)],
        provider_token='',  # empty = Telegram Stars
    )


DONATION_MIN_STARS = 1
DONATION_MAX_STARS = 100_000


async def _handle_donate(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_stars: str) -> None:
    """Send a Stars invoice for a donation initiated via deep-link (browser fallback)."""
    try:
        stars = int(raw_stars)
    except (TypeError, ValueError):
        stars = 0
    if stars < DONATION_MIN_STARS or stars > DONATION_MAX_STARS:
        await update.message.reply_text('❌ Некорректная сумма доната.')
        return

    tg = update.effective_user
    await _link_tg_user(tg.id, tg.username or '', tg.first_name or '', None,
                        _norm_locale(tg.language_code))

    await update.message.reply_invoice(
        title='✨ Поддержать Tarot Online',
        description=f'Спасибо за поддержку проекта! Ваш дар: {stars} ⭐',
        payload=f'donate|{stars}|0',
        currency='XTR',
        prices=[LabeledPrice(f'{stars} ⭐', stars)],
        provider_token='',  # empty = Telegram Stars
    )


async def pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    parts = query.invoice_payload.split('|')
    if len(parts) != 3 or parts[0] not in ('buy', 'donate'):
        await query.answer(ok=False, error_message='Ошибка платежа. Попробуй ещё раз.')
        return
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.message.successful_payment
    payer_id = update.effective_user.id if update.effective_user else None
    charge_id = payment.telegram_payment_charge_id
    # Always log payer + charge id so a payment can be looked up / refunded later
    # (refund needs payer tg_id + telegram_payment_charge_id).
    log.info(
        'STARS PAYMENT ok: payer_tg_id=%s charge_id=%s amount=%s payload=%s',
        payer_id, charge_id, payment.total_amount, payment.invoice_payload,
    )

    parts = payment.invoice_payload.split('|')
    if len(parts) != 3:
        log.error('unexpected invoice payload: %s', payment.invoice_payload)
        return

    # Donations grant no entitlement — just say thank you.
    if parts[0] == 'donate':
        stars = parts[1]
        await update.message.reply_text(
            f"✨ Спасибо за поддержку! Твой дар в {stars} ⭐ согревает проект.\n"
            "Пусть карты будут к тебе благосклонны. 🌙",
            parse_mode='Markdown',
        )
        return

    _, plan_slug, user_id_str = parts

    try:
        plan_name = await _activate(int(user_id_str), plan_slug, charge_id)
        webapp_url = getattr(settings, 'WEBAPP_URL', 'https://sokirdon.com')
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🌙 Открыть приложение",
                web_app=WebAppInfo(url=webapp_url),
            ),
        ]])
        await update.message.reply_text(
            f"✨ Подписка *{plan_name}* активирована!\n\n"
            "Premium уже доступен. Нажми кнопку ниже, чтобы открыть приложение. 🌙",
            parse_mode='Markdown',
            reply_markup=keyboard,
        )
    except Exception:
        log.exception('activate failed charge=%s user=%s plan=%s', charge_id, user_id_str, plan_slug)
        await update.message.reply_text(
            f"⚠️ Оплата прошла, но возникла ошибка активации.\n"
            f"Напиши в поддержку с кодом: `{charge_id}`",
            parse_mode='Markdown',
        )
