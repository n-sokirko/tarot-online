"""Views for reading sessions."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.readings.models import Interpretation, Reading
from apps.readings.serializers import (
    CreateReadingSerializer,
    InterpretationSerializer,
    ReadingSerializer,
)
from services.ai import client as ai_client
from services.ai import prompts as ai_prompts


def _format_user_message(reading: Reading) -> str:
    """Compose the user-turn content for the AI: question + drawn cards."""
    locale = reading.locale
    spread = reading.spread_type
    cards = list(reading.cards.select_related('card').order_by('position_index'))
    positions = spread.positions or []

    lines = []
    question = reading.question.strip() or (
        'Открытый вопрос — без формулировки.' if locale == 'ru'
        else 'Open question — no specific framing.'
    )
    lines.append(f'Вопрос: {question}' if locale == 'ru' else f'Question: {question}')
    lines.append('')
    lines.append(f'Расклад: {spread.name_ru if locale == "ru" else spread.name_en}'
                 if locale == 'ru' else
                 f'Spread: {spread.name_en}')
    lines.append('')
    for rc in cards:
        pos = positions[rc.position_index] if rc.position_index < len(positions) else {}
        pos_label = (
            pos.get('label_ru' if locale == 'ru' else 'label_en')
            or f'Position {rc.position_index + 1}'
        )
        card = rc.card
        card_name = card.name_ru if locale == 'ru' else card.name_en
        meaning = card.upright_meaning_ru if locale == 'ru' else card.upright_meaning_en
        keywords = card.keywords_ru if locale == 'ru' else card.keywords_en
        lines.append(f'• {pos_label}: {card_name}')
        lines.append(f'  Ключи: {", ".join(keywords)}' if locale == 'ru'
                     else f'  Keywords: {", ".join(keywords)}')
        lines.append(f'  Значение: {meaning}' if locale == 'ru'
                     else f'  Meaning: {meaning}')
        lines.append('')

    if locale == 'ru':
        lines.append('Напиши интерпретацию по правилам системного промпта.')
    else:
        lines.append('Write the interpretation following the rules of the system prompt.')
    return '\n'.join(lines)


class ReadingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST /api/v1/readings/                  — create a new reading
    GET  /api/v1/readings/{id}/             — retrieve a reading by id
    POST /api/v1/readings/{id}/interpret/   — request AI interpretation
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return Reading.objects.select_related('spread_type', 'interpretation').prefetch_related(
            'cards', 'cards__card'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReadingSerializer
        return ReadingSerializer

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            return self.get_queryset().get(pk=pk)
        except Reading.DoesNotExist:
            raise NotFound(detail=f"Reading {pk} not found.")

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = CreateReadingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reading = serializer.save()

        # Attach the authenticated user when present (anonymous still allowed).
        if getattr(request, 'user', None) and request.user.is_authenticated:
            reading.user = request.user
            reading.save(update_fields=['user'])

        reading = (
            Reading.objects.select_related('spread_type', 'interpretation')
            .prefetch_related('cards', 'cards__card')
            .get(pk=reading.pk)
        )
        output = ReadingSerializer(reading)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='interpret')
    def interpret(self, request: Request, pk=None) -> Response:
        """Generate an AI interpretation for the reading. Synchronous for MVP.

        Accepts optional ``question`` in the request body — the user's story,
        context, or specific question.  If provided, ``reading.question`` is
        updated **before** the prompt is built so the AI can weave its
        response around the user's narrative.

        - Tier resolved from authenticated user. Anonymous → free tier (Haiku).
        - Free tier on Haiku is permitted; premium uses Sonnet.
        - Credits are charged via billing.services. Free users without credits
          are still allowed for now (we'll add a daily limit before launch);
          authenticated premium with empty wallet falls back to allowance.
        - Idempotent: if an Interpretation already exists, return it.
        """
        reading = self.get_object()

        # ── Accept user question / story ─────────────────────────────
        question = (request.data.get('question') or '').strip()
        if question and not hasattr(reading, 'interpretation'):
            reading.question = question
            reading.save(update_fields=['question'])

        if hasattr(reading, 'interpretation'):
            return Response(
                InterpretationSerializer(reading.interpretation).data,
                status=status.HTTP_200_OK,
            )

        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

        # Decide which tier (and therefore which model) to use.
        info = billing.tier_for(user)
        tier = info.tier
        model = ai_client.model_for_tier(tier)

        # Charge credits before generating, so over-quota free users get a clean 402.
        charged, balance = billing.charge_credits(
            user=user,
            kind=UsageLedger.KIND_AI_TAROT,
            model_used=model,
            reference_id=f'reading:{reading.pk}',
        )
        if not charged:
            return Response(
                {
                    'detail': 'out_of_credits',
                    'message_ru': 'Закончились бесплатные интерпретации. Оформи Premium или купи кредиты.',
                    'message_en': 'No credits left. Subscribe to Premium or buy a credit pack.',
                    'balance': balance,
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        try:
            base_prompt = ai_prompts.base_system(reading.locale)
            spread_prompt = ai_prompts.tarot_spread(reading.spread_type.slug, reading.locale)
            user_msg = _format_user_message(reading)
            result = ai_client.generate_interpretation(
                base_system_prompt=base_prompt,
                spread_system_prompt=spread_prompt,
                user_message=user_msg,
                model=model,
                max_tokens=1800,
                temperature=0.85,
            )
        except RuntimeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        interpretation = Interpretation.objects.create(
            reading=reading,
            body_md=result.body,
            model_used=result.model,
            prompt_version=ai_prompts.PROMPT_VERSION,
            token_count=result.input_tokens + result.output_tokens,
        )

        return Response(
            InterpretationSerializer(interpretation).data,
            status=status.HTTP_201_CREATED,
        )
