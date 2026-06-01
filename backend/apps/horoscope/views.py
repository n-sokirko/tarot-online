"""Daily horoscope API views.

GET  /api/v1/horoscope/signs/              — list 12 zodiac signs (metadata)
GET  /api/v1/horoscope/{sign}/             — free deterministic daily horoscope
GET  /api/v1/horoscope/{sign}/?date=YYYY-MM-DD
POST /api/v1/horoscope/{sign}/interpret/   — premium AI deep daily reading
"""
from __future__ import annotations

import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.horoscope import services as horo_svc
from apps.horoscope.models import HoroscopeAIReading
from apps.horoscope.serializers import HoroscopeAIReadingSerializer
from services.ai import client as ai_client
from services.ai import prompts as ai_prompts


def _locale_from(request: Request) -> str:
    loc = (request.query_params.get("locale") or "ru").lower()
    return "ru" if loc not in ("ru", "en") else loc


def _parse_date(request: Request) -> datetime.date:
    raw = request.query_params.get("date")
    if raw:
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            pass
    return timezone.localdate()


class HoroscopeSignsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        locale = _locale_from(request)
        return Response({"signs": horo_svc.list_signs(locale)})


class HoroscopeDailyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, sign: str) -> Response:
        sign = sign.lower()
        if sign not in horo_svc.VALID_SLUGS:
            return Response(
                {"detail": "unknown_sign", "valid": sorted(horo_svc.VALID_SLUGS)},
                status=status.HTTP_404_NOT_FOUND,
            )
        locale = _locale_from(request)
        date = _parse_date(request)
        return Response(horo_svc.daily_horoscope(sign, date, locale))


class HoroscopeInterpretView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request, sign: str) -> Response:
        sign = sign.lower()
        if sign not in horo_svc.VALID_SLUGS:
            return Response(
                {"detail": "unknown_sign", "valid": sorted(horo_svc.VALID_SLUGS)},
                status=status.HTTP_404_NOT_FOUND,
            )

        locale = (request.data.get("locale") or "ru").lower()
        locale = "ru" if locale not in ("ru", "en") else locale
        date = timezone.localdate()

        # Serve cached reading if it exists (no double charge).
        cached = HoroscopeAIReading.objects.filter(sign=sign, date=date, locale=locale).first()
        if cached is not None:
            return Response(HoroscopeAIReadingSerializer(cached).data)

        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

        # The AI horoscope is cheap (1 credit) and does NOT require a subscription —
        # any logged-in user with credits can buy it; premium users get it included.
        if user is None:
            return Response(
                {
                    "detail": "login_required",
                    "message_ru": "Войди, чтобы открыть подробный AI-гороскоп.",
                    "message_en": "Sign in to unlock the detailed AI horoscope.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tier = billing.tier_for(user).tier
        model = ai_client.model_for_tier(tier)

        charged, balance = billing.charge_credits(
            user=user,
            kind=UsageLedger.KIND_AI_HOROSCOPE,  # cheap: 1 credit
            model_used=model,
            reference_id=f"horoscope:{sign}:{date.isoformat()}",
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

        horo = horo_svc.daily_horoscope(sign, date, locale)
        try:
            base_prompt = ai_prompts.base_system(locale)
            horo_prompt = ai_prompts.horoscope(locale)
            user_msg = horo_svc.format_horoscope_for_ai(horo, locale)
            result = ai_client.generate_interpretation(
                base_system_prompt=base_prompt,
                spread_system_prompt=horo_prompt,
                user_message=user_msg,
                model=model,
                max_tokens=1400,
                temperature=0.85,
            )
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        reading, _ = HoroscopeAIReading.objects.get_or_create(
            sign=sign, date=date, locale=locale,
            defaults={"body_md": result.body, "model_used": result.model},
        )
        return Response(HoroscopeAIReadingSerializer(reading).data, status=status.HTTP_201_CREATED)
