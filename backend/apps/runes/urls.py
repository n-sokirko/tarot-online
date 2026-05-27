"""URL routing for runes."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.runes import views

router = SimpleRouter()
router.register(r'runes/casts', views.RuneCastViewSet, basename='rune-cast')

urlpatterns = [
    path('runes/', views.runes_list, name='runes-list'),
] + router.urls
