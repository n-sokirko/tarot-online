"""Natal chart API views."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.natal.models import NatalChart, NatalInterpretation
from apps.natal.serializers import (
    CreateNatalChartSerializer,
    NatalChartSerializer,
    NatalInterpretationSerializer,
)
from apps.natal import services as natal_svc
from services.ai import client as ai_client
from services.ai import prompts as ai_prompts


class NatalChartViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST /api/v1/natal/charts/           — create chart (geocode + calculate)
    GET  /api/v1/natal/charts/{id}/      — retrieve saved chart
    POST /api/v1/natal/charts/{id}/interpret/ — AI interpretation
    """
    permission_classes = [AllowAny]
    # Keep default JWT authentication so authenticated users can be identified
    # (used for premium tier gating), but don't require it (AllowAny above).

    def get_queryset(self):
        return NatalChart.objects.select_related("interpretation")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateNatalChartSerializer
        return NatalChartSerializer

    def get_object(self):
        pk = self.kwargs["pk"]
        try:
            return self.get_queryset().get(pk=pk)
        except NatalChart.DoesNotExist:
            raise NotFound(detail=f"NatalChart {pk} not found.")

    def create(self, request: Request, *args, **kwargs) -> Response:
        ser = CreateNatalChartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Determine premium status
        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        is_premium = user is not None and billing.has_entitlement(user, "natal_chart")

        # Geocode city
        try:
            lat, lng, tz_str = natal_svc.geocode_city(data["birth_city"])
        except ValueError as exc:
            return Response(
                {"detail": "city_not_found", "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate chart
        try:
            result = natal_svc.calculate_chart(
                birth_date=data["birth_date"],
                birth_time=data.get("birth_time"),
                lat=lat,
                lng=lng,
                tz_str=tz_str,
                name=data.get("birth_name", ""),
                is_premium=is_premium,
            )
        except Exception as exc:
            return Response(
                {"detail": "calculation_error", "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        chart = NatalChart.objects.create(
            user=user,
            birth_name=data.get("birth_name", ""),
            birth_date=data["birth_date"],
            birth_time=data.get("birth_time"),
            birth_city=data["birth_city"],
            birth_lat=lat,
            birth_lng=lng,
            birth_tz=tz_str,
            locale=data.get("locale", "ru"),
            planets=result["planets"],
            houses=result["houses"],
            aspects=result["aspects"],
            ascendant=result["ascendant"],
        )

        return Response(NatalChartSerializer(chart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="interpret")
    def interpret(self, request: Request, pk=None) -> Response:
        chart = self.get_object()

        if chart.interpretation_id is not None:
            return Response(NatalInterpretationSerializer(chart.interpretation).data)

        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

        # Interpret requires the natal_chart entitlement (premium feature).
        if not billing.has_entitlement(user, "natal_chart"):
            return Response(
                {
                    "detail": "premium_required",
                    "required_entitlement": "natal_chart",
                    "message_ru": "AI-интерпретация натальной карты доступна по Premium-подписке.",
                    "message_en": "AI interpretation of the natal chart is available with a Premium subscription.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        tier = billing.tier_for(user).tier
        model = ai_client.model_for_tier(tier)

        charged, balance = billing.charge_credits(
            user=user,
            kind=UsageLedger.KIND_AI_NATAL,
            model_used=model,
            reference_id=f"natal_chart:{chart.pk}",
        )
        if not charged:
            return Response(
                {
                    "detail": "out_of_credits",
                    "message_ru": "Закончились кредиты. Оформи Premium или купи кредиты.",
                    "message_en": "No credits left. Subscribe to Premium or buy a credit pack.",
                    "balance": balance,
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        locale = chart.locale or "ru"
        try:
            base_prompt = ai_prompts.base_system(locale)
            natal_prompt = ai_prompts.natal_chart(locale)
            user_msg = natal_svc.format_chart_for_ai(chart, locale)
            result = ai_client.generate_interpretation(
                base_system_prompt=base_prompt,
                spread_system_prompt=natal_prompt,
                user_message=user_msg,
                model=model,
                max_tokens=2000,
                temperature=0.82,
            )
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        interpretation = NatalInterpretation.objects.create(
            body_md=result.body,
            model_used=result.model,
        )
        chart.interpretation = interpretation
        chart.save(update_fields=["interpretation"])

        return Response(
            NatalInterpretationSerializer(interpretation).data,
            status=status.HTTP_201_CREATED,
        )
