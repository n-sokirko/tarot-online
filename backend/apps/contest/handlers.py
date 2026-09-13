"""Telegram bot handlers for the contest flow."""
import logging

from asgiref.sync import sync_to_async
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from apps.contest import services as contest_services
from apps.telegram_bot.gate import requires_channel_sub

log = logging.getLogger(__name__)


def _norm_locale(language_code) -> str:
    return 'ru' if str(language_code or '').startswith('ru') else 'en'


@sync_to_async
def _upsert_tg_user(tg_id: int, username: str, first_name: str, locale: str):
    from apps.telegram_bot.models import TelegramUser
    obj, _ = TelegramUser.objects.update_or_create(
        tg_id=tg_id,
        defaults={'tg_username': username, 'tg_first_name': first_name, 'locale': locale},
    )
    return obj


@sync_to_async
def _active_contest(channel=None):
    return contest_services.active_contest(channel=channel)


@sync_to_async
def _get_or_create_entry(contest, tg_user):
    return contest_services.get_or_create_entry(contest, tg_user)


@sync_to_async
def _register_invite_link(entry, url):
    contest_services.register_invite_link(entry, url)


@sync_to_async
def _entry_stats(entry):
    return contest_services.entry_stats(entry)


@sync_to_async
def _leaderboard(contest, limit=10):
    rows = list(contest_services.leaderboard(contest, limit=limit))
    return [(e.tg_user.tg_username or str(e.tg_user.tg_id), e.invites_count) for e in rows]


@sync_to_async
def _record_invite(invite_link_name, invited_tg_id):
    return contest_services.record_invite(invite_link_name, invited_tg_id)


# ── /contest ──────────────────────────────────────────────────────────────────

async def contest_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shared entry for `/contest` AND the `?start=contest` deep link from the
    channel post's «Участвовать» button. Idempotent: re-entering the same user
    returns their existing invite link + current stats, never a duplicate entry."""
    tg = update.effective_user
    locale = _norm_locale(tg.language_code)
    contest = await _active_contest()
    if not contest:
        msg = ("🎁 Сейчас активных конкурсов нет. Загляни позже!"
               if locale == 'ru' else
               "🎁 No active contests right now. Check back soon!")
        await update.message.reply_text(msg)
        return

    user = await _upsert_tg_user(tg.id, tg.username or '', tg.first_name or '', locale)
    entry, created = await _get_or_create_entry(contest, user)

    if created or not entry.invite_link_url:
        try:
            link = await context.bot.create_chat_invite_link(
                chat_id=contest.channel,
                name=entry.invite_link_name,
                creates_join_request=False,
            )
            await _register_invite_link(entry, link.invite_link)
            entry.invite_link_url = link.invite_link
        except Exception as e:  # noqa: BLE001 — surface to user, don't crash
            log.exception("create_chat_invite_link failed: %s", e)
            err = ("Не получилось создать персональную ссылку. Бот должен быть "
                   "админом в канале с правом приглашать. Напиши админу — поправим."
                   if locale == 'ru' else
                   "Couldn't create your personal link. The bot needs admin rights "
                   "in the channel to invite users.")
            await update.message.reply_text(err)
            return

    stats = await _entry_stats(entry)
    prize = f"Premium · {contest.prize_months} мес." if locale == 'ru' \
            else f"Premium · {contest.prize_months} mo."
    if locale == 'ru':
        text = (
            f"🎁 *Конкурс «{contest.title}»*\n\n"
            f"Призы: *{contest.prize_count} × {prize}*\n"
            f"Условие: пригласи минимум *{contest.min_invites}* друзей в канал.\n"
            f"До розыгрыша: <ends_at>\n\n"
            f"🔗 *Твоя ссылка:*\n`{entry.invite_link_url}`\n\n"
            f"📊 Приглашено: *{stats['invites_count']}*   "
            f"Место: *#{stats['rank']}* из {stats['total_participants']}\n\n"
            f"_Победителей выберет случайный жеребий из тех, кто набрал ≥ "
            f"{contest.min_invites} приглашений._"
        )
        btn = "🏆 Топ участников"
    else:
        text = (
            f"🎁 *Contest «{contest.title}»*\n\n"
            f"Prizes: *{contest.prize_count} × {prize}*\n"
            f"Condition: invite at least *{contest.min_invites}* friends to the channel.\n\n"
            f"🔗 *Your link:*\n`{entry.invite_link_url}`\n\n"
            f"📊 Invited: *{stats['invites_count']}*   "
            f"Rank: *#{stats['rank']}* of {stats['total_participants']}\n\n"
            f"_Winners are drawn at random from entries with ≥ "
            f"{contest.min_invites} invites._"
        )
        btn = "🏆 Leaderboard"

    text = text.replace('<ends_at>', contest.ends_at.strftime('%d.%m.%Y'))
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(btn, callback_data='contest:top')]])
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)


@requires_channel_sub
async def contest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`/contest` command wrapper — gated by channel-sub requirement."""
    await contest_join(update, context)


# ── /contest_top ──────────────────────────────────────────────────────────────

async def _send_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    locale = _norm_locale(tg.language_code)
    contest = await _active_contest()
    if not contest:
        msg = ("Конкурс ещё не запущен." if locale == 'ru' else "No active contest.")
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    top = await _leaderboard(contest, limit=10)
    if not top:
        body = "Пока никто не пригласил никого — будь первым!" if locale == 'ru' \
               else "Nobody has invited anyone yet — be first!"
    else:
        lines = []
        for i, (uname, n) in enumerate(top, start=1):
            medal = '🥇🥈🥉'[i-1] if i <= 3 else f' {i}.'
            handle = f'@{uname}' if not uname.isdigit() else f'id{uname}'
            lines.append(f"{medal} {handle} — *{n}*")
        body = '\n'.join(lines)

    title = f"🏆 *Топ конкурса «{contest.title}»*" if locale == 'ru' \
            else "🏆 *Contest leaderboard*"
    text = f"{title}\n\n{body}"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')


@requires_channel_sub
async def contest_top_command(update, context):
    await _send_top(update, context)


async def contest_top_callback(update, context):
    await _send_top(update, context)


# ── chat_member: tally invites ────────────────────────────────────────────────

async def on_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fires when channel membership changes. If it's a 'just joined' event and
    the join carried one of our contest invite links, count it."""
    cm = update.chat_member
    if cm is None:
        return
    new_status = cm.new_chat_member.status if cm.new_chat_member else None
    old_status = cm.old_chat_member.status if cm.old_chat_member else None
    if new_status not in ('member', 'restricted'):
        return  # only count fresh joins
    if old_status in ('member', 'restricted', 'administrator', 'creator'):
        return  # already in, status change only

    link = cm.invite_link
    if link is None or not link.name:
        return
    invited_id = cm.new_chat_member.user.id
    await _record_invite(link.name, invited_id)
