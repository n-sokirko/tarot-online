"""Serializers for reading session models."""
import random

from rest_framework import serializers

from apps.readings.models import Reading, ReadingCard
from apps.tarot.models import Card, SpreadType
from apps.tarot.serializers import CardSerializer, SpreadTypeSerializer


class ReadingCardSerializer(serializers.ModelSerializer):
    position_index = serializers.IntegerField()
    is_reversed = serializers.BooleanField()
    card = CardSerializer(read_only=True)

    class Meta:
        model = ReadingCard
        fields = ['position_index', 'is_reversed', 'card']


class ReadingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    question = serializers.CharField()
    locale = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    spread_type = SpreadTypeSerializer(read_only=True)
    cards = ReadingCardSerializer(many=True, read_only=True)

    class Meta:
        model = Reading
        fields = ['id', 'question', 'locale', 'created_at', 'spread_type', 'cards']


class CreateReadingSerializer(serializers.Serializer):
    question = serializers.CharField(
        allow_blank=True,
        trim_whitespace=True,
        default='',
    )
    locale = serializers.ChoiceField(choices=['ru', 'en'])
    spread_slug = serializers.SlugField()

    def validate_spread_slug(self, value: str) -> SpreadType:
        try:
            return SpreadType.objects.get(slug=value)
        except SpreadType.DoesNotExist:
            raise serializers.ValidationError(
                f"Spread '{value}' not found."
            )

    def create(self, validated_data: dict) -> Reading:
        spread_type: SpreadType = validated_data['spread_slug']
        question: str = validated_data['question']
        locale: str = validated_data['locale']

        card_ids = list(Card.objects.values_list('id', flat=True))
        if len(card_ids) < spread_type.positions_count:
            raise serializers.ValidationError(
                'Not enough cards in the deck to fill this spread.'
            )

        chosen_ids = random.sample(card_ids, spread_type.positions_count)
        cards_map = {c.id: c for c in Card.objects.filter(id__in=chosen_ids)}

        reading = Reading.objects.create(
            spread_type=spread_type,
            question=question,
            locale=locale,
        )

        reading_cards = [
            ReadingCard(
                reading=reading,
                card=cards_map[card_id],
                position_index=idx,
                is_reversed=random.random() < 0.5,
            )
            for idx, card_id in enumerate(chosen_ids)
        ]
        ReadingCard.objects.bulk_create(reading_cards)

        return reading
