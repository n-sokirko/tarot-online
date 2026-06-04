"""Admin: Telegram users + broadcast sending."""
from django.conf import settings
from django.contrib import admin, messages
from django.utils import timezone

from apps.telegram_bot.models import Broadcast, TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('tg_id', 'tg_username', 'tg_first_name', 'user', 'daily_push', 'created_at')
    list_filter = ('daily_push', 'created_at')
    search_fields = ('tg_username', 'tg_first_name', 'tg_id')
    actions = ['enable_push', 'disable_push']

    @admin.action(description='🔔 Включить ежедневный пуш')
    def enable_push(self, request, queryset):
        n = queryset.update(daily_push=True)
        self.message_user(request, f'Включено для {n} пользователей.')

    @admin.action(description='🔕 Выключить ежедневный пуш')
    def disable_push(self, request, queryset):
        n = queryset.update(daily_push=False)
        self.message_user(request, f'Выключено для {n} пользователей.')


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'target', 'sent_count', 'failed_count', 'sent_at', 'created_at')
    list_filter = ('target', 'sent_at')
    search_fields = ('title', 'message')
    readonly_fields = ('sent_at', 'sent_count', 'failed_count', 'created_at')
    actions = ['send_now']

    @admin.action(description='📤 Отправить выбранные рассылки')
    def send_now(self, request, queryset):
        import requests

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.message_user(request, 'TELEGRAM_BOT_TOKEN не настроен.', level=messages.ERROR)
            return

        for bc in queryset:
            recipients = TelegramUser.objects.all()
            if bc.target == Broadcast.TARGET_SUBSCRIBERS:
                recipients = recipients.filter(daily_push=True)
            sent = failed = 0
            for u in recipients:
                try:
                    r = requests.post(
                        f'https://api.telegram.org/bot{token}/sendMessage',
                        json={'chat_id': u.tg_id, 'text': bc.message, 'parse_mode': 'Markdown'},
                        timeout=15,
                    )
                    if r.ok and r.json().get('ok'):
                        sent += 1
                    else:
                        failed += 1
                except Exception:  # noqa: BLE001 — best-effort; count and continue
                    failed += 1
            bc.sent_count = sent
            bc.failed_count = failed
            bc.sent_at = timezone.now()
            bc.save(update_fields=['sent_count', 'failed_count', 'sent_at'])
            self.message_user(
                request,
                f'Рассылка «{bc}»: отправлено {sent}, ошибок {failed}.',
                level=messages.SUCCESS if sent else messages.WARNING,
            )
