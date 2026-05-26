"""Serializers for tarot domain models."""
from rest_framework import serializers

from apps.tarot.models import Card, SpreadType


class CardSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField()
    suit = serializers.CharField()
    number = serializers.IntegerField()
    name_ru = serializers.CharField()
    name_en = serializers.CharField()
    keywords_ru = serializers.JSONField()
    keywords_en = serializers.JSONField()
    image_url = serializers.CharField()
    upright_meaning_ru = serializers.CharField()
    upright_meaning_en = serializers.CharField()
    reversed_meaning_ru = serializers.CharField()
    reversed_meaning_en = serializers.CharField()

    class Meta:
        model = Card
        fields = [
            'slug',
            'suit',
            'number',
            'name_ru',
            'name_en',
            'keywords_ru',
            'keywords_en',
            'image_url',
            'upright_meaning_ru',
            'upright_meaning_en',
            'reversed_meaning_ru',
            'reversed_meaning_en',
        ]


class SpreadTypeSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField()
    name_ru = serializers.CharField()
    name_en = serializers.CharField()
    positions_count = serializers.IntegerField()
    positions = serializers.JSONField()

    class Meta:
        model = SpreadType
        fields = [
            'slug',
            'name_ru',
            'name_en',
            'positions_count',
            'positions',
        ]
