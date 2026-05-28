"""Serializers for the natal chart API."""
from rest_framework import serializers

from apps.natal.models import NatalChart, NatalInterpretation


class NatalInterpretationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NatalInterpretation
        fields = ["id", "body_md", "model_used", "generated_at"]


class NatalChartSerializer(serializers.ModelSerializer):
    interpretation = NatalInterpretationSerializer(read_only=True)

    class Meta:
        model = NatalChart
        fields = [
            "id",
            "birth_name",
            "birth_date",
            "birth_time",
            "birth_city",
            "birth_lat",
            "birth_lng",
            "birth_tz",
            "locale",
            "planets",
            "houses",
            "aspects",
            "ascendant",
            "interpretation",
            "created_at",
        ]
        read_only_fields = [
            "id", "birth_lat", "birth_lng", "birth_tz",
            "planets", "houses", "aspects", "ascendant",
            "interpretation", "created_at",
        ]


class CreateNatalChartSerializer(serializers.Serializer):
    birth_name = serializers.CharField(max_length=128, allow_blank=True, default="")
    birth_date = serializers.DateField()
    birth_time = serializers.TimeField(allow_null=True, required=False)
    birth_city = serializers.CharField(max_length=128)
    locale = serializers.ChoiceField(choices=["ru", "en"], default="ru")
