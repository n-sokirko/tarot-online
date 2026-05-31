"""Serializers for the horoscope API."""
from rest_framework import serializers

from apps.horoscope.models import HoroscopeAIReading


class HoroscopeAIReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoroscopeAIReading
        fields = ["id", "sign", "date", "locale", "body_md", "model_used", "generated_at"]
