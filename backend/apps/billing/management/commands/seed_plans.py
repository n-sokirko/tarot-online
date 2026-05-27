"""
Management command: seed_plans

Seeds the three default plans: Free, Premium ($5/mo), Credit packs ($3 / $10).
Idempotent. Paddle product/price ids are read from env so the same code works
in sandbox and production.

Usage:
    python manage.py seed_plans
"""
from django.core.management.base import BaseCommand
from decouple import config

from apps.billing.models import Plan


PLANS = [
    {
        "slug": "free",
        "name_ru": "Бесплатный",
        "name_en": "Free",
        "description_ru": "3 расклада Таро в день, базовые описания, без AI-интерпретации.",
        "description_en": "3 tarot readings per day, base descriptions, no AI interpretation.",
        "kind": Plan.KIND_FREE,
        "price_usd_cents": 0,
        "monthly_included_credits": 0,
        "credits_granted": 0,
        "entitlement_keys": [],
        "sort_order": 0,
        "_env_product": None,
        "_env_price": None,
    },
    {
        "slug": "premium-monthly",
        "name_ru": "Premium · в месяц",
        "name_en": "Premium · monthly",
        "description_ru": "50 AI-интерпретаций в месяц на модели Sonnet, расклад Кельтского креста, расклады на рунах, безлимитная история.",
        "description_en": "50 AI interpretations per month on Sonnet, Celtic Cross spread, rune casts, unlimited history.",
        "kind": Plan.KIND_SUBSCRIPTION,
        "price_usd_cents": 500,
        "monthly_included_credits": 50,
        "credits_granted": 0,
        "entitlement_keys": ["premium_spreads", "sonnet_ai", "celtic_cross", "runes_ai", "history_unlimited"],
        "sort_order": 10,
        "_env_product": "PADDLE_PRODUCT_PREMIUM_MONTHLY",
        "_env_price": "PADDLE_PRICE_PREMIUM_MONTHLY",
    },
    {
        "slug": "credits-small",
        "name_ru": "10 кредитов",
        "name_en": "10 credits",
        "description_ru": "Разовая покупка 10 кредитов. Подходит для углублённых раскладов и натальной карты.",
        "description_en": "One-time purchase of 10 credits. Good for deep readings and natal charts.",
        "kind": Plan.KIND_CREDITS,
        "price_usd_cents": 300,
        "monthly_included_credits": 0,
        "credits_granted": 10,
        "entitlement_keys": [],
        "sort_order": 20,
        "_env_product": "PADDLE_PRODUCT_CREDITS_SMALL",
        "_env_price": "PADDLE_PRICE_CREDITS_SMALL",
    },
    {
        "slug": "credits-large",
        "name_ru": "50 кредитов",
        "name_en": "50 credits",
        "description_ru": "Разовая покупка 50 кредитов. Лучшая цена за единицу.",
        "description_en": "One-time purchase of 50 credits. Best per-credit price.",
        "kind": Plan.KIND_CREDITS,
        "price_usd_cents": 1000,
        "monthly_included_credits": 0,
        "credits_granted": 50,
        "entitlement_keys": [],
        "sort_order": 30,
        "_env_product": "PADDLE_PRODUCT_CREDITS_LARGE",
        "_env_price": "PADDLE_PRICE_CREDITS_LARGE",
    },
]


class Command(BaseCommand):
    help = "Seed billing plans (free, premium, credit packs)."

    def handle(self, *args, **options) -> None:
        count = 0
        for raw in PLANS:
            plan = dict(raw)
            product_env = plan.pop("_env_product")
            price_env = plan.pop("_env_price")
            paddle_product_id = config(product_env, default="") if product_env else ""
            paddle_price_id = config(price_env, default="") if price_env else ""

            Plan.objects.update_or_create(
                slug=plan["slug"],
                defaults={
                    **{k: v for k, v in plan.items() if k != "slug"},
                    "paddle_product_id": paddle_product_id,
                    "paddle_price_id": paddle_price_id,
                    "is_active": True,
                },
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {count} plans."))
