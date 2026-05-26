"""URL routing for the tarot app."""
from rest_framework.routers import SimpleRouter

from apps.tarot.views import CardViewSet, SpreadTypeViewSet

router = SimpleRouter()
router.register(r'cards', CardViewSet, basename='card')
router.register(r'spreads', SpreadTypeViewSet, basename='spread')

urlpatterns = router.urls
