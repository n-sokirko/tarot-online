"""
Management command: create a test user with full Premium access.

Usage:
    python manage.py create_test_premium_user

Creates (or updates) user test@sokirdon.com with password Test1234!
and grants all current entitlements + 100 credits.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

EMAIL = 'test@sokirdon.com'
PASSWORD = 'Test1234!'
DISPLAY_NAME = 'Test Premium User'

ENTITLEMENTS = [
    'sonnet_ai',
    'celtic_cross',
    'runes_ai',
    'history_unlimited',
    'natal_chart',
    'premium_spreads',
]


class Command(BaseCommand):
    help = 'Create (or reset) test@sokirdon.com with full Premium access.'

    def handle(self, *args, **options) -> None:
        from apps.billing.models import (
            CreditWallet, Entitlement, Plan, Subscription,
        )

        # ── User ──────────────────────────────────────────────────────────────
        user, created = User.objects.update_or_create(
            email=EMAIL,
            defaults={
                'username': EMAIL,
                'display_name': DISPLAY_NAME,
                'is_active': True,
            },
        )
        user.set_password(PASSWORD)
        user.save(update_fields=['password'])
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} user: {EMAIL}')

        # ── Subscription ──────────────────────────────────────────────────────
        try:
            plan = Plan.objects.get(slug='premium-monthly')
        except Plan.DoesNotExist:
            self.stderr.write('Plan premium-monthly not found — run seed_plans first.')
            return

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'provider': Subscription.PROVIDER_TELEGRAM,
                'tg_payment_charge_id': 'test_charge_000',
                'status': Subscription.STATUS_ACTIVE,
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timedelta(days=365),
            },
        )
        self.stdout.write('Subscription: premium-monthly (active, 1 year)')

        # ── Entitlements ──────────────────────────────────────────────────────
        for key in ENTITLEMENTS:
            Entitlement.objects.update_or_create(
                user=user,
                key=key,
                defaults={'expires_at': None, 'source': 'test'},
            )
        self.stdout.write(f'Entitlements: {", ".join(ENTITLEMENTS)}')

        # ── Credits ───────────────────────────────────────────────────────────
        wallet, _ = CreditWallet.objects.get_or_create(user=user)
        wallet.balance = 100
        wallet.save(update_fields=['balance', 'updated_at'])
        self.stdout.write('Credits: 100')

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Test user ready:\n'
            f'  Email:    {EMAIL}\n'
            f'  Password: {PASSWORD}\n'
            f'  Tier:     Premium (all entitlements)\n'
            f'  Credits:  100\n'
        ))
