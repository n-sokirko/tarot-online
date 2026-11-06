"""URL routing for the readings app."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.readings.views import ReadingViewSet
from apps.readings.views_profile import TarologistForgetView, TarologistView

router = SimpleRouter()
router.register(r'readings', ReadingViewSet, basename='reading')

urlpatterns = [
    path('tarologist/', TarologistView.as_view(), name='tarologist'),
    path('tarologist/forget/', TarologistForgetView.as_view(), name='tarologist-forget'),
    *router.urls,
]
