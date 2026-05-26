"""URL routing for the readings app."""
from rest_framework.routers import SimpleRouter

from apps.readings.views import ReadingViewSet

router = SimpleRouter()
router.register(r'readings', ReadingViewSet, basename='reading')

urlpatterns = router.urls
