"""Admin: users."""
from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'display_name', 'locale', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'locale', 'date_joined')
    search_fields = ('email', 'display_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
