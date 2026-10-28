"""Admin: readings, with the cards drawn and the AI's answer on the same page.

The interpretation is stored with the model that wrote it and the prompt version
(`services.ai.prompts.PROMPT_VERSION`), so the admin is where to read what the
model actually said and judge whether a prompt change helped.
"""
from django.contrib import admin

from apps.readings.models import Interpretation, Reading, ReadingCard


class ReadingCardInline(admin.TabularInline):
    model = ReadingCard
    extra = 0
    can_delete = False
    fields = ('position_index', 'card', 'is_reversed')
    readonly_fields = ('position_index', 'card', 'is_reversed')
    ordering = ('position_index',)

    def has_add_permission(self, request, obj=None) -> bool:
        return False


class InterpretationInline(admin.StackedInline):
    model = Interpretation
    extra = 0
    can_delete = False
    fields = ('model_used', 'prompt_version', 'token_count', 'generated_at', 'body_md')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'spread_type', 'short_question', 'interpreted',
                    'answer_model', 'prompt_version', 'created_at')
    list_filter = ('spread_type', 'locale', 'interpretation__model_used',
                   'interpretation__prompt_version', 'created_at')
    search_fields = ('question', 'user__email', 'interpretation__body_md')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'spread_type', 'interpretation')
    inlines = [ReadingCardInline, InterpretationInline]

    @admin.display(description='Вопрос')
    def short_question(self, obj):
        return (obj.question or '—')[:50]

    @admin.display(boolean=True, description='Разбор')
    def interpreted(self, obj):
        return hasattr(obj, 'interpretation')

    @admin.display(description='Модель', ordering='interpretation__model_used')
    def answer_model(self, obj):
        return obj.interpretation.model_used if hasattr(obj, 'interpretation') else '—'

    @admin.display(description='Версия промпта', ordering='interpretation__prompt_version')
    def prompt_version(self, obj):
        return obj.interpretation.prompt_version if hasattr(obj, 'interpretation') else '—'
