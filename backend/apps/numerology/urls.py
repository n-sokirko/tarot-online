"""URL config for numerology app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.numerology.views import NumerologyViewSet

router = DefaultRouter()
router.register(r"numerology/readings", NumerologyViewSet, basename="numerology-reading")

urlpatterns = [
    path("", include(router.urls)),
]
