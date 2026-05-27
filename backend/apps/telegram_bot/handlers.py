"""Telegram bot handlers: /start, /status, invoice flow, successful_payment."""
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update, WebAppInfo
from telegram.ext import ContextTypes

from apps.telegram_bot.tokens import validate_payment_token

log = logging.getLogger(__name__)

# ── DB helpers (sync → async wrappers) ────────────────────────────────────────

@sync_to_async
def _get_plan(slug: str):
    from apps.billing.models import Plan
    return Plan.objects.get(slug=slug, is_active=True, tg_stars_price__gt=0)


@sync_to_async
def _link_tg_user(tg_id: int, tg_username: str, tg_first_name: str, user_id: int | None):
    from apps.telegram_bot.models import TelegramUser
    defaults = {'tg_username': tg_username, 'tg_first_name': tg_first_name}
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


# ── Handlers ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if args and args[0].startswith('buy_'):
        await _handle_buy(update, context, args[0][4:])
        return

    webapp_url = getattr(settings, 'WEBAPP_URL', 'https://sokirdon.com')
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🌙 Открыть расклады",
            web_app=WebAppInfo(url=webapp_url),
        ),
    ]])

    await update.message.reply_text(
        "🌙 *Tarot Online Bot*\n\n"
        "Нажми кнопку ниже, чтобы открыть расклады прямо в Telegram — "
        "без регистрации, всё сохраняется в аккаунт автоматически.\n\n"
        "Здесь также можно оплатить Premium-подписку через Telegram Stars ⭐\n\n"
        "/status — проверить подписку",
        parse_mode='Markdown',
        reply_markup=keyboard,
    )


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
    await _link_tg_user(tg.id, tg.username or '', tg.first_name or '', user_id)

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


async def pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    parts = query.invoice_payload.split('|')
    if len(parts) != 3 or parts[0] != 'buy':
        await query.answer(ok=False, error_message='Ошибка платежа. Попробуй ещё раз.')
        return
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.message.successful_payment
    parts = payment.invoice_payload.split('|')
    if len(parts) != 3:
        log.error('unexpected invoice payload: %s', payment.invoice_payload)
        return

    _, plan_slug, user_id_str = parts
    charge_id = payment.telegram_payment_charge_id

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
