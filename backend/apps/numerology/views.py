"""Numerology API views."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.numerology.models import NumerologyInterpretation, NumerologyReading
from apps.numerology.serializers import (
    CreateNumerologyReadingSerializer,
    NumerologyInterpretationSerializer,
    NumerologyReadingSerializer,
)
from apps.numerology import services as num_svc
from services.ai import client as ai_client
from services.ai import prompts as ai_prompts


class NumerologyViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST /api/v1/numerology/readings/                  — create reading
    GET  /api/v1/numerology/readings/{id}/             — retrieve
    POST /api/v1/numerology/readings/{id}/interpret/   — AI interpretation
    """
    permission_classes = [AllowAny]

    def get_queryset(self):
        return NumerologyReading.objects.select_related("interpretation")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateNumerologyReadingSerializer
        return NumerologyReadingSerializer

    def get_object(self):
        pk = self.kwargs["pk"]
        try:
            return self.get_queryset().get(pk=pk)
        except NumerologyReading.DoesNotExist:
            raise NotFound(detail=f"NumerologyReading {pk} not found.")

    def create(self, request: Request, *args, **kwargs) -> Response:
        ser = CreateNumerologyReadingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        profile = num_svc.calculate_profile(data["full_name"], data["birth_date"])

        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        reading = NumerologyReading.objects.create(
            user=user,
            full_name=data["full_name"],
            birth_date=data["birth_date"],
            locale=data.get("locale", "ru"),
            **profile,
        )

        return Response(NumerologyReadingSerializer(reading).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="interpret")
    def interpret(self, request: Request, pk=None) -> Response:
        reading = self.get_object()

        if reading.interpretation_id is not None:
            return Response(NumerologyInterpretationSerializer(reading.interpretation).data)

        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        tier = billing.tier_for(user).tier
        model = ai_client.model_for_tier(tier)

        charged, balance = billing.charge_credits(
            user=user,
            kind=UsageLedger.KIND_AI_NATAL,  # reuse natal cost tier (3 credits)
            model_used=model,
            reference_id=f"numerology:{reading.pk}",
        )
        if not charged:
            return Response({
                "detail": "out_of_credits",
                "message_ru": "Закончились кредиты. Оформи Premium или купи кредиты.",
                "message_en": "No credits left. Subscribe to Premium or buy a credit pack.",
                "balance": balance,
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        locale = reading.locale or "ru"
        try:
            base_prompt = ai_prompts.base_system(locale)
            num_prompt = ai_prompts.numerology(locale)
            profile = {
                "life_path": reading.life_path,
                "destiny": reading.destiny,
                "soul_urge": reading.soul_urge,
                "personality": reading.personality,
                "birthday": reading.birthday,
            }
            user_msg = num_svc.format_profile_for_ai(profile, reading.full_name, reading.birth_date, locale)
            result = ai_client.generate_interpretation(
                base_system_prompt=base_prompt,
                spread_system_prompt=num_prompt,
                user_message=user_msg,
                model=model,
                max_tokens=1800,
                temperature=0.82,
            )
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        interpretation = NumerologyInterpretation.objects.create(
            body_md=result.body, model_used=result.model,
        )
        reading.interpretation = interpretation
        reading.save(update_fields=["interpretation"])
        return Response(NumerologyInterpretationSerializer(interpretation).data, status=status.HTTP_201_CREATED)
