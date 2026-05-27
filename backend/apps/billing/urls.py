"""URL routing for billing."""
from django.urls import path

from apps.billing import views

urlpatterns = [
    path('billing/plans/', views.plans_list, name='billing-plans'),
    path('billing/me/', views.billing_me, name='billing-me'),
    path('billing/checkout/', views.checkout, name='billing-checkout'),
    path('billing/checkout/telegram/', views.telegram_checkout, name='billing-checkout-telegram'),
    path('billing/checkout/telegram-invoice/', views.telegram_invoice, name='billing-checkout-telegram-invoice'),
    path('billing/webhooks/paddle/', views.paddle_webhook, name='billing-webhook-paddle'),
]
