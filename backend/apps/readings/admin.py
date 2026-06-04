"""Admin: readings."""
from django.contrib import admin

from apps.readings.models import Reading


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'spread_type', 'short_question', 'interpreted', 'created_at')
    list_filter = ('spread_type', 'locale', 'created_at')
    search_fields = ('question', 'user__email')
    date_hierarchy = 'created_at'

    @admin.display(description='Вопрос')
    def short_question(self, obj):
        return (obj.question or '—')[:50]

    @admin.display(boolean=True, description='Разбор')
    def interpreted(self, obj):
        return hasattr(obj, 'interpretation')
