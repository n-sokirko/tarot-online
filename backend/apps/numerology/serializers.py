"""Serializers for numerology API."""
from rest_framework import serializers

from apps.numerology.models import NumerologyInterpretation, NumerologyReading


class NumerologyInterpretationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumerologyInterpretation
        fields = ["id", "body_md", "model_used", "generated_at"]


class NumerologyReadingSerializer(serializers.ModelSerializer):
    interpretation = NumerologyInterpretationSerializer(read_only=True)
    titles = serializers.SerializerMethodField()
    life_path_summary = serializers.SerializerMethodField()

    class Meta:
        model = NumerologyReading
        fields = [
            "id", "full_name", "birth_date", "locale",
            "life_path", "destiny", "soul_urge", "personality", "birthday",
            "titles", "life_path_summary",
            "interpretation", "created_at",
        ]
        read_only_fields = [
            "id", "life_path", "destiny", "soul_urge", "personality", "birthday",
            "titles", "life_path_summary",
            "interpretation", "created_at",
        ]

    def get_titles(self, obj):
        from apps.numerology.services import SHORT_TITLES_RU, SHORT_TITLES_EN
        titles = SHORT_TITLES_RU if obj.locale == "ru" else SHORT_TITLES_EN
        return {
            "life_path": titles.get(obj.life_path, "—"),
            "destiny": titles.get(obj.destiny, "—"),
            "soul_urge": titles.get(obj.soul_urge, "—"),
            "personality": titles.get(obj.personality, "—"),
            "birthday": titles.get(obj.birthday, "—"),
        }

    def get_life_path_summary(self, obj):
        from apps.numerology.services import LIFE_PATH_TEXT_RU, LIFE_PATH_TEXT_EN
        text = LIFE_PATH_TEXT_RU if obj.locale == "ru" else LIFE_PATH_TEXT_EN
        return text.get(obj.life_path, "")


class CreateNumerologyReadingSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=128)
    birth_date = serializers.DateField()
    locale = serializers.ChoiceField(choices=["ru", "en"], default="ru")
