"""Runes API views."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.billing.rate_limit import ANON_DAILY_LIMIT, check_anon_daily_limit
from apps.runes.models import Rune, RuneCast, RuneInterpretation
from apps.runes.serializers import (
    CreateRuneCastSerializer,
    LAYOUT_POSITIONS,
    RuneCastSerializer,
    RuneInterpretationSerializer,
    RuneSerializer,
)
from services.ai import client as ai_client
from services.ai import prompts as ai_prompts


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def runes_list(_request: Request) -> Response:
    runes = Rune.objects.all().order_by('number')
    return Response({'runes': RuneSerializer(runes, many=True).data})


def _format_rune_user_message(cast: RuneCast) -> str:
    locale = cast.locale
    positions = LAYOUT_POSITIONS.get(cast.layout, [])
    items = list(cast.items.select_related('rune').order_by('position_index'))

    lines = []
    question = cast.question.strip() or (
        'Открытый вопрос — без формулировки.' if locale == 'ru'
        else 'Open question — no specific framing.'
    )
    lines.append(f'Вопрос: {question}' if locale == 'ru' else f'Question: {question}')
    lines.append('')
    layout_name = {
        'single': ('Одна руна', 'Single rune'),
        'three': ('Три руны', 'Three runes'),
        'five': ('Пятиричный крест', 'Five-rune cross'),
    }[cast.layout]
    lines.append(f'Бросок: {layout_name[0 if locale == "ru" else 1]}')
    lines.append('')
    for item in items:
        pos = positions[item.position_index] if item.position_index < len(positions) else {}
        label = pos.get('label_ru' if locale == 'ru' else 'label_en', f'#{item.position_index + 1}')
        rune = item.rune
        name = rune.name_ru if locale == 'ru' else rune.name_en
        meaning = rune.meaning_ru if locale == 'ru' else rune.meaning_en
        keywords = rune.keywords_ru if locale == 'ru' else rune.keywords_en
        lines.append(f'• {label}: {rune.symbol} {name}')
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


class RuneCastViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST /api/v1/runes/casts/             — make a rune cast
    GET  /api/v1/runes/casts/{id}/        — retrieve a cast
    POST /api/v1/runes/casts/{id}/interpret/ — request AI interpretation
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return RuneCast.objects.select_related('interpretation').prefetch_related('items', 'items__rune')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRuneCastSerializer
        return RuneCastSerializer

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            return self.get_queryset().get(pk=pk)
        except RuneCast.DoesNotExist:
            raise NotFound(detail=f'RuneCast {pk} not found.')

    def create(self, request: Request, *args, **kwargs) -> Response:
        ser = CreateRuneCastSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cast = ser.save()
        if getattr(request, 'user', None) and request.user.is_authenticated:
            cast.user = request.user
            cast.save(update_fields=['user'])
        cast = self.get_queryset().get(pk=cast.pk)
        return Response(RuneCastSerializer(cast).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='interpret')
    def interpret(self, request: Request, pk=None) -> Response:
        cast = self.get_object()

        # Accept user question / story before interpreting.
        question = (request.data.get('question') or '').strip()
        if question and not hasattr(cast, 'interpretation'):
            cast.question = question
            cast.save(update_fields=['question'])

        # Require a question to avoid burning tokens on empty prompts.
        if not cast.question.strip() and not hasattr(cast, 'interpretation'):
            return Response({
                'detail': 'question_required',
                'message_ru': 'Напиши свой вопрос, чтобы руны могли ответить.',
                'message_en': 'Write your question so the runes can respond.',
            }, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(cast, 'interpretation'):
            return Response(RuneInterpretationSerializer(cast.interpretation).data)

        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

        # Anonymous users: enforce daily free limit before hitting the AI.
        if user is None:
            allowed, remaining = check_anon_daily_limit(request, kind='runes')
            if not allowed:
                return Response({
                    'detail': 'rate_limited',
                    'message_ru': (
                        f'Ты уже использовал {ANON_DAILY_LIMIT} бесплатных интерпретации сегодня. '
                        'Войди или зарегистрируйся — это бесплатно.'
                    ),
                    'message_en': (
                        f"You've used all {ANON_DAILY_LIMIT} free interpretations for today. "
                        "Log in or sign up — it's free."
                    ),
                }, status=429)

        tier = billing.tier_for(user).tier
        model = ai_client.model_for_tier(tier)

        charged, balance = billing.charge_credits(
            user=user,
            kind=UsageLedger.KIND_AI_RUNES,
            model_used=model,
            reference_id=f'rune_cast:{cast.pk}',
        )
        if not charged:
            return Response({
                'detail': 'out_of_credits',
                'message_ru': 'Закончились бесплатные интерпретации. Оформи Premium или купи кредиты.',
                'message_en': 'No credits left. Subscribe to Premium or buy a credit pack.',
                'balance': balance,
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        try:
            base_prompt = ai_prompts.base_system(cast.locale)
            runes_prompt = ai_prompts.runes_cast(cast.locale)
            user_msg = _format_rune_user_message(cast)
            result = ai_client.generate_interpretation(
                base_system_prompt=base_prompt,
                spread_system_prompt=runes_prompt,
                user_message=user_msg,
                model=model,
                max_tokens=1500,
                temperature=0.85,
            )
        except RuntimeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        interpretation = RuneInterpretation.objects.create(
            cast=cast,
            body_md=result.body,
            model_used=result.model,
            prompt_version=ai_prompts.PROMPT_VERSION,
            token_count=result.input_tokens + result.output_tokens,
        )
        return Response(
            RuneInterpretationSerializer(interpretation).data,
            status=status.HTTP_201_CREATED,
        )
