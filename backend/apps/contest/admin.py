"""Django admin for contests — create/manage contests and draw winners."""
import logging

from django.contrib import admin, messages
from django.db.models import Count, Q

from apps.contest.models import Contest, ContestEntry, ContestInvite
from apps.contest import services as contest_services

log = logging.getLogger(__name__)


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'channel', 'status', 'starts_at', 'ends_at',
        'prize_count', 'prize_months', 'min_invites', 'entries_count',
    )
    list_filter = ('status', 'channel')
    search_fields = ('title', 'channel')
    readonly_fields = ('winners_drawn_at', 'created_at')
    actions = ['activate_contests', 'draw_winners_now', 'grant_all_prizes', 'notify_winners']

    @admin.display(description='Участников')
    def entries_count(self, obj):
        return obj.entries.count()

    @admin.action(description='✅ Активировать выбранные конкурсы')
    def activate_contests(self, request, queryset):
        n = queryset.update(status=Contest.STATUS_ACTIVE)
        self.message_user(request, f'Активировано: {n}.')

    @admin.action(description='🎲 Провести розыгрыш (случайно выбрать победителей)')
    def draw_winners_now(self, request, queryset):
        for contest in queryset:
            winners = contest_services.draw_winners(contest)
            if not winners:
                self.message_user(
                    request,
                    f'«{contest.title}»: нет участников с ≥ {contest.min_invites} приглашениями.',
                    level=messages.WARNING,
                )
                continue
            handles = ', '.join(
                f'@{w.tg_user.tg_username or w.tg_user.tg_id}' for w in winners
            )
            self.message_user(
                request,
                f'«{contest.title}»: победители ({len(winners)}): {handles}',
                level=messages.SUCCESS,
            )

    @admin.action(description='🎁 Выдать премиум всем победителям')
    def grant_all_prizes(self, request, queryset):
        for contest in queryset:
            winners = contest.entries.filter(is_winner=True)
            granted = 0
            skipped = 0
            for w in winners:
                if contest_services.grant_prize(w):
                    granted += 1
                else:
                    skipped += 1
            self.message_user(
                request,
                f'«{contest.title}»: выдано {granted}, пропущено {skipped} '
                f'(уже выдано / нет связанного Django-юзера).',
                level=messages.SUCCESS if granted else messages.WARNING,
            )

    @admin.action(description='📣 Уведомить победителей в личку')
    def notify_winners(self, request, queryset):
        """Best-effort: requires TELEGRAM_BOT_TOKEN to be set. Uses sync requests
        rather than the async bot — admin runs in a sync request cycle."""
        from django.conf import settings
        import requests
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if not token:
            self.message_user(request, 'TELEGRAM_BOT_TOKEN не настроен.', level=messages.ERROR)
            return
        for contest in queryset:
            winners = contest.entries.filter(is_winner=True).select_related('tg_user')
            sent = failed = 0
            for w in winners:
                is_ru = (w.tg_user.locale or 'ru').startswith('ru')
                if is_ru:
                    text = (
                        f"🎉 *Поздравляем!* Ты в числе победителей конкурса "
                        f"«{contest.title}» и получаешь Premium на "
                        f"{contest.prize_months} мес. Уже активирован — открой /status."
                    )
                else:
                    text = (
                        f"🎉 *Congratulations!* You won the «{contest.title}» contest "
                        f"and got {contest.prize_months}-month Premium. "
                        f"Already active — check /status."
                    )
                try:
                    r = requests.post(
                        f'https://api.telegram.org/bot{token}/sendMessage',
                        json={'chat_id': w.tg_user.tg_id, 'text': text, 'parse_mode': 'Markdown'},
                        timeout=15,
                    )
                    if r.ok and r.json().get('ok'):
                        sent += 1
                    else:
                        failed += 1
                except Exception:  # noqa: BLE001
                    failed += 1
            self.message_user(
                request,
                f'«{contest.title}»: уведомлено {sent}, ошибок {failed}.',
                level=messages.SUCCESS if sent else messages.WARNING,
            )


@admin.register(ContestEntry)
class ContestEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest', 'tg_user', 'invites_count', 'is_winner',
                    'prize_granted_at', 'created_at')
    list_filter = ('contest', 'is_winner')
    search_fields = ('tg_user__tg_username', 'tg_user__tg_first_name')
    readonly_fields = ('invite_link_url', 'invite_link_name', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('contest', 'tg_user')
        return qs.annotate(
            _invites_count=Count('invites', filter=Q(invites__still_member=True))
        )

    @admin.display(description='Приглашений', ordering='_invites_count')
    def invites_count(self, obj):
        return obj._invites_count


@admin.register(ContestInvite)
class ContestInviteAdmin(admin.ModelAdmin):
    list_display = ('entry', 'invited_tg_id', 'still_member', 'joined_at')
    list_filter = ('still_member',)
    search_fields = ('invited_tg_id',)
