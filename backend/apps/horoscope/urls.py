"""URL config for the horoscope app."""
from django.urls import path

from apps.horoscope.views import (
    HoroscopeDailyView,
    HoroscopeInterpretView,
    HoroscopeSignsView,
)

urlpatterns = [
    path("horoscope/signs/", HoroscopeSignsView.as_view(), name="horoscope-signs"),
    path("horoscope/<str:sign>/", HoroscopeDailyView.as_view(), name="horoscope-daily"),
    path("horoscope/<str:sign>/interpret/", HoroscopeInterpretView.as_view(), name="horoscope-interpret"),
]
