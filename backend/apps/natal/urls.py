"""URL config for the natal chart app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.natal.views import NatalChartViewSet

router = DefaultRouter()
router.register(r"natal/charts", NatalChartViewSet, basename="natal-chart")

urlpatterns = [
    path("", include(router.urls)),
]
