"""Serializers for billing endpoints."""
from rest_framework import serializers

from apps.billing.models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'slug', 'name_ru', 'name_en', 'description_ru', 'description_en',
            'kind', 'price_usd_cents',
            'monthly_included_credits', 'credits_granted',
            'entitlement_keys', 'paddle_price_id',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_slug = serializers.CharField(source='plan.slug', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'plan_slug', 'status', 'current_period_start', 'current_period_end',
            'canceled_at',
        ]


class BillingMeSerializer(serializers.Serializer):
    tier = serializers.CharField()
    credits = serializers.IntegerField()
    entitlements = serializers.ListField(child=serializers.CharField())
    subscription = SubscriptionSerializer(allow_null=True)
