"""Admin: billing (plans, subscriptions, credits, usage)."""
from django.contrib import admin

from apps.billing.models import (
    CreditWallet,
    Entitlement,
    Plan,
    Subscription,
    UsageLedger,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name_ru', 'kind', 'tg_stars_price', 'monthly_included_credits', 'credits_granted', 'is_active')
    list_filter = ('kind', 'is_active')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'provider', 'current_period_end', 'created_at')
    list_filter = ('status', 'provider')
    search_fields = ('user__email',)
    date_hierarchy = 'created_at'


@admin.register(CreditWallet)
class CreditWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__email',)


@admin.register(UsageLedger)
class UsageLedgerAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'cost_credits', 'model_used', 'created_at')
    list_filter = ('kind',)
    search_fields = ('user__email', 'reference_id')
    date_hierarchy = 'created_at'


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'source', 'expires_at')
    list_filter = ('key', 'source')
    search_fields = ('user__email',)
