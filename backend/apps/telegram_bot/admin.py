"""Admin: Telegram users + broadcast sending."""
from django.conf import settings
from django.contrib import admin, messages
from django.utils import timezone

from apps.telegram_bot.models import Broadcast, ChannelPost, TelegramUser


@admin.register(ChannelPost)
class ChannelPostAdmin(admin.ModelAdmin):
    """Read-only log of what the channel autoposter has published.

    Editing makes no sense — the post is already in Telegram — but this list is
    the fastest way to see whether the generator is drifting or repeating itself.
    """
    list_display = ('created_at', 'kind', 'topic', 'status', 'attempts')
    list_filter = ('kind', 'status', 'created_at')
    search_fields = ('topic', 'text')
    readonly_fields = ('kind', 'topic', 'text', 'fingerprint', 'status', 'published_at',
                       'tg_message_id', 'error', 'model_used', 'input_tokens',
                       'output_tokens', 'attempts', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request) -> bool:
        return False


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('tg_id', 'tg_username', 'tg_first_name', 'user', 'daily_push',
                    'bot_blocked', 'last_send_error', 'birth_date', 'zodiac', 'created_at')
    list_filter = ('bot_blocked', 'daily_push', 'created_at')
    search_fields = ('tg_username', 'tg_first_name', 'tg_id')
    actions = ['check_reachable', 'enable_push', 'disable_push', 'send_card_now',
               'send_horoscope_now']

    @admin.action(description='📡 Проверить, доходят ли сообщения (выбранным)')
    def check_reachable(self, request, queryset):
        from apps.telegram_bot import delivery

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.message_user(request, 'TELEGRAM_BOT_TOKEN не настроен.', level=messages.ERROR)
            return
        ok_n, bad = 0, []
        for u in queryset:
            ok, err = delivery.probe(token, u.tg_id)
            delivery.record(u, ok, err)
            if ok:
                ok_n += 1
            else:
                bad.append(f'{u.tg_id} @{u.tg_username or u.tg_first_name}: {delivery.explain(err)}')
        self.message_user(
            request,
            f'Доходит: {ok_n}, не доходит: {len(bad)}. Подробности в колонке «Last send error».',
            level=messages.SUCCESS if not bad else messages.WARNING,
        )

    @admin.display(description='Знак')
    def zodiac(self, obj):
        """Zodiac label from the stored birth date (not the natal chart, to keep
        the changelist query-free)."""
        if not obj.birth_date:
            return '—'
        from apps.horoscope.services import sign_for_date
        s = sign_for_date(obj.birth_date.month, obj.birth_date.day)
        return f"{s['symbol']} {s['name_ru']}" if s else '—'

    @admin.action(description='🔔 Включить ежедневный пуш')
    def enable_push(self, request, queryset):
        n = queryset.update(daily_push=True)
        self.message_user(request, f'Включено для {n} пользователей.')

    @admin.action(description='🔕 Выключить ежедневный пуш')
    def disable_push(self, request, queryset):
        n = queryset.update(daily_push=False)
        self.message_user(request, f'Выключено для {n} пользователей.')

    @admin.action(description='🌙 Отправить карту дня (выбранным)')
    def send_card_now(self, request, queryset):
        from apps.telegram_bot.push import send_card_push
        result = send_card_push(queryset)
        if result.get('error'):
            self.message_user(request, result['error'], level=messages.ERROR)
            return
        self.message_user(
            request,
            f"Карта дня: отправлено {result['sent']}, ошибок {result['failed']}.",
            level=messages.SUCCESS if result['sent'] else messages.WARNING,
        )

    @admin.action(description='🔮 Отправить гороскоп (выбранным)')
    def send_horoscope_now(self, request, queryset):
        from apps.telegram_bot.push import send_horoscope_push
        result = send_horoscope_push(queryset.select_related('user'))
        if result.get('error'):
            self.message_user(request, result['error'], level=messages.ERROR)
            return
        self.message_user(
            request,
            f"Гороскоп: отправлено {result['sent']}, "
            f"пропущено {result['skipped']} (нет даты рождения), ошибок {result['failed']}.",
            level=messages.SUCCESS if result['sent'] else messages.WARNING,
        )


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'target', 'sent_count', 'failed_count', 'sent_at', 'created_at')
    list_filter = ('target', 'sent_at')
    search_fields = ('title', 'message')
    readonly_fields = ('sent_at', 'sent_count', 'failed_count', 'failed_detail', 'created_at')
    actions = ['send_now']

    @admin.action(description='📤 Отправить выбранные рассылки')
    def send_now(self, request, queryset):
        from apps.telegram_bot import delivery

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.message_user(request, 'TELEGRAM_BOT_TOKEN не настроен.', level=messages.ERROR)
            return

        for bc in queryset:
            recipients = TelegramUser.objects.all()
            if bc.target == Broadcast.TARGET_SUBSCRIBERS:
                recipients = recipients.filter(daily_push=True)
            sent, failed_lines = 0, []
            for u in recipients:
                ok, err = delivery.send_text(token, u.tg_id, bc.message)
                delivery.record(u, ok, err)
                if ok:
                    sent += 1
                else:
                    failed_lines.append(
                        f'{u.tg_id} @{u.tg_username or u.tg_first_name}: {delivery.explain(err)}')
            bc.sent_count = sent
            bc.failed_count = len(failed_lines)
            bc.failed_detail = '\n'.join(failed_lines)
            bc.sent_at = timezone.now()
            bc.save(update_fields=['sent_count', 'failed_count', 'failed_detail', 'sent_at'])
            self.message_user(
                request,
                f'Рассылка «{bc}»: отправлено {sent}, ошибок {len(failed_lines)}. '
                f'Кому не дошло — внутри рассылки, поле «Failed detail».',
                level=messages.SUCCESS if sent else messages.WARNING,
            )
