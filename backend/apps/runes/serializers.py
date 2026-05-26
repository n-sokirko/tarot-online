"""Serializers for runes."""
import random

from rest_framework import serializers

from apps.runes.models import Rune, RuneCast, RuneCastItem, RuneInterpretation


# Position labels per layout (no separate DB table for runes — layouts are simpler than tarot spreads).
LAYOUT_POSITIONS = {
    'single': [
        {'label_ru': 'Знак', 'label_en': 'Sign'},
    ],
    'three': [
        {'label_ru': 'Что есть сейчас', 'label_en': 'What is now'},
        {'label_ru': 'Что нужно', 'label_en': 'What is needed'},
        {'label_ru': 'Куда смотреть', 'label_en': 'Where to look'},
    ],
    'five': [
        {'label_ru': 'Прошлое', 'label_en': 'Past'},
        {'label_ru': 'Настоящее', 'label_en': 'Present'},
        {'label_ru': 'Скрытое влияние', 'label_en': 'Hidden influence'},
        {'label_ru': 'Совет', 'label_en': 'Advice'},
        {'label_ru': 'Возможный исход', 'label_en': 'Possible outcome'},
    ],
}
LAYOUT_COUNTS = {'single': 1, 'three': 3, 'five': 5}


class RuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rune
        fields = ['slug', 'number', 'aett', 'symbol',
                  'name_ru', 'name_en', 'meaning_ru', 'meaning_en',
                  'keywords_ru', 'keywords_en']


class RuneCastItemSerializer(serializers.ModelSerializer):
    rune = RuneSerializer(read_only=True)

    class Meta:
        model = RuneCastItem
        fields = ['position_index', 'rune']


class RuneInterpretationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuneInterpretation
        fields = ['body_md', 'model_used', 'prompt_version', 'generated_at', 'token_count']


class RuneCastSerializer(serializers.ModelSerializer):
    items = RuneCastItemSerializer(many=True, read_only=True)
    interpretation = RuneInterpretationSerializer(read_only=True)
    positions = serializers.SerializerMethodField()

    class Meta:
        model = RuneCast
        fields = ['id', 'layout', 'question', 'locale', 'created_at',
                  'positions', 'items', 'interpretation']

    def get_positions(self, obj: RuneCast):
        return LAYOUT_POSITIONS.get(obj.layout, [])


class CreateRuneCastSerializer(serializers.Serializer):
    question = serializers.CharField(allow_blank=True, default='', trim_whitespace=True)
    locale = serializers.ChoiceField(choices=['ru', 'en'])
    layout = serializers.ChoiceField(choices=['single', 'three', 'five'], default='three')

    def create(self, validated_data: dict) -> RuneCast:
        layout = validated_data['layout']
        count = LAYOUT_COUNTS[layout]

        rune_ids = list(Rune.objects.values_list('id', flat=True))
        if len(rune_ids) < count:
            raise serializers.ValidationError('Not enough runes seeded.')
        chosen = random.sample(rune_ids, count)

        cast = RuneCast.objects.create(
            layout=layout,
            question=validated_data['question'],
            locale=validated_data['locale'],
        )
        RuneCastItem.objects.bulk_create([
            RuneCastItem(cast=cast, rune_id=rune_id, position_index=idx)
            for idx, rune_id in enumerate(chosen)
        ])
        return cast
