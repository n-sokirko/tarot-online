"""URL routing for the tarot app."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.tarot.views import CardViewSet, SpreadTypeViewSet
from apps.tarot.ritual import RitualCheckinView, RitualView
from apps.tarot.tts_views import tts_synthesize

router = SimpleRouter()
router.register(r'cards', CardViewSet, basename='card')
router.register(r'spreads', SpreadTypeViewSet, basename='spread')

urlpatterns = router.urls + [
    path('tts/', tts_synthesize, name='tts-synthesize'),
    # The daily ritual behind the home screen's streak and week grid.
    path('ritual/', RitualView.as_view(), name='ritual'),
    path('ritual/checkin/', RitualCheckinView.as_view(), name='ritual-checkin'),
]
