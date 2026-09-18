"""Views for reading sessions."""
import json
import random

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing import services as billing
from apps.billing.models import UsageLedger
from apps.billing.rate_limit import ANON_DAILY_LIMIT, check_anon_daily_limit
from apps.readings.models import Interpretation, Reading, ReadingCard
from apps.readings.serializers import (
    CreateReadingSerializer,
    InterpretationSerializer,
    ReadingCardSerializer,
    ReadingSerializer,
)
from apps.tarot.models import Card, SpreadType
from services.ai import client as ai_client
from services.ai import prompts as ai_prompts


def _sse(payload: dict) -> str:
    """Format one Server-Sent Event line."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _placement_ru(rc) -> str:
    """Coarse spot on the table, so the AI can talk about the arrangement.

    Exact coordinates would be noise — what matters for a reading is whether a
    card sits to the left of another, or apart at the bottom.
    """
    col = 'слева' if rc.x < 0.34 else ('справа' if rc.x > 0.66 else 'по центру')
    row = 'вверху' if rc.y < 0.34 else ('внизу' if rc.y > 0.66 else 'в середине')
    return f'{row}, {col}'


def _placement_en(rc) -> str:
    col = 'left' if rc.x < 0.34 else ('right' if rc.x > 0.66 else 'centre')
    row = 'top' if rc.y < 0.34 else ('bottom' if rc.y > 0.66 else 'middle')
    return f'{row}, {col}'


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
    # The free table has no positions at all: the person decided the shape, so
    # the arrangement itself is what the AI has to read.
    free_table = not positions
    if free_table:
        lines.append(
            'Позиций нет — человек сам выложил карты на стол в удобном ему порядке. '
            'Читай саму раскладку: в каком порядке легли карты и как они стоят '
            'относительно друг друга.'
            if locale == 'ru' else
            'There are no fixed positions — the person laid the cards out on the table '
            'themselves. Read the arrangement: the order they were placed and how they '
            'sit relative to one another.'
        )
        lines.append('')
    for rc in cards:
        pos = positions[rc.position_index] if rc.position_index < len(positions) else {}
        if free_table:
            pos_label = (
                f'Карта {rc.position_index + 1} ({_placement_ru(rc)})' if locale == 'ru'
                else f'Card {rc.position_index + 1} ({_placement_en(rc)})'
            )
        else:
            pos_label = (
                pos.get('label_ru' if locale == 'ru' else 'label_en')
                or f'Position {rc.position_index + 1}'
            )
        card = rc.card
        card_name = card.name_ru if locale == 'ru' else card.name_en
        # Respect the orientation: on the free table the person turns cards
        # themselves, and sending the upright text for a reversed card would
        # quietly throw that choice away.
        if rc.is_reversed:
            meaning = card.reversed_meaning_ru if locale == 'ru' else card.reversed_meaning_en
            card_name += ' (перевёрнута)' if locale == 'ru' else ' (reversed)'
        else:
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

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request: Request) -> Response:
        """The authenticated user's reading history (journal), newest first."""
        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        if user is None:
            return Response({'detail': 'authentication_required'}, status=status.HTTP_401_UNAUTHORIZED)
        qs = self.get_queryset().filter(user=user).order_by('-created_at')[:50]
        return Response(ReadingSerializer(qs, many=True).data)

    # Spread slugs that require an active entitlement to draw.
    PREMIUM_SPREADS = {
        'celtic-cross': 'celtic_cross',
    }

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = CreateReadingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Premium gating — block creation of premium spreads for users without
        # the matching entitlement (anonymous users are blocked too).
        spread_slug = (request.data.get('spread_slug') or '').strip()
        required_key = self.PREMIUM_SPREADS.get(spread_slug)
        if required_key:
            user = (
                request.user
                if getattr(request, 'user', None) and request.user.is_authenticated
                else None
            )
            if not billing.has_entitlement(user, required_key):
                return Response(
                    {
                        'detail': 'premium_required',
                        'required_entitlement': required_key,
                        'message_ru': 'Этот расклад доступен по Premium-подписке.',
                        'message_en': 'This spread is available with a Premium subscription.',
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

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

    # ── Free table ────────────────────────────────────────────────────────────
    # A reading with no predefined positions: the person pulls cards from the
    # deck one at a time and arranges them wherever they want. Which card comes
    # up stays with the server — only the placing and the orientation are theirs,
    # so the draw cannot be re-rolled from the client.

    FREE_TABLE_SLUG = 'free-table'
    # A ceiling, not a rule of the spread: it keeps one table from growing into a
    # prompt that costs a fortune to interpret.
    MAX_TABLE_CARDS = 12

    @staticmethod
    def _clamp01(value, default=0.5) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return default

    @action(detail=False, methods=['post'], url_path='table')
    def table(self, request: Request) -> Response:
        """Open an empty free table. Cards arrive one by one through `draw`."""
        locale = request.data.get('locale')
        if locale not in ('ru', 'en'):
            return Response({'detail': 'locale must be ru or en'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            spread = SpreadType.objects.get(slug=self.FREE_TABLE_SLUG)
        except SpreadType.DoesNotExist:
            return Response({'detail': 'free-table spread is not seeded'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        reading = Reading.objects.create(
            spread_type=spread,
            question=(request.data.get('question') or '').strip(),
            locale=locale,
            user=request.user if getattr(request, 'user', None)
            and request.user.is_authenticated else None,
        )
        reading = self.get_queryset().get(pk=reading.pk)
        return Response(ReadingSerializer(reading).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='draw')
    def draw(self, request: Request, pk=None) -> Response:
        """Pull the next card onto the table at the given spot."""
        reading = self.get_object()
        if reading.spread_type.slug != self.FREE_TABLE_SLUG:
            return Response(
                {'detail': 'not_a_free_table',
                 'message_ru': 'Карты можно вытягивать только на свободном столе.',
                 'message_en': 'Cards can only be drawn onto a free table.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        x = self._clamp01(request.data.get('x'))
        y = self._clamp01(request.data.get('y'))
        is_reversed = bool(request.data.get('is_reversed', False))

        # Locked so two quick taps cannot race for the same position_index, which
        # the unique_together would reject.
        with transaction.atomic():
            locked = Reading.objects.select_for_update().get(pk=reading.pk)
            drawn = list(locked.cards.values_list('card_id', 'position_index'))
            if len(drawn) >= self.MAX_TABLE_CARDS:
                return Response(
                    {'detail': 'table_full',
                     'message_ru': f'На столе уже {self.MAX_TABLE_CARDS} карт — больше не помещается.',
                     'message_en': f'The table already holds {self.MAX_TABLE_CARDS} cards.'},
                    status=status.HTTP_409_CONFLICT,
                )
            used_ids = {card_id for card_id, _ in drawn}
            remaining = list(Card.objects.exclude(id__in=used_ids).values_list('id', flat=True))
            if not remaining:
                return Response({'detail': 'deck_exhausted'}, status=status.HTTP_409_CONFLICT)

            rc = ReadingCard.objects.create(
                reading=locked,
                card_id=random.choice(remaining),
                position_index=len(drawn),
                is_reversed=is_reversed,
                x=x,
                y=y,
            )

        rc = ReadingCard.objects.select_related('card').get(pk=rc.pk)
        return Response(ReadingCardSerializer(rc).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='layout')
    def layout(self, request: Request, pk=None) -> Response:
        """Persist where the cards ended up after being moved around."""
        reading = self.get_object()
        if reading.spread_type.slug != self.FREE_TABLE_SLUG:
            return Response({'detail': 'not_a_free_table'}, status=status.HTTP_400_BAD_REQUEST)

        items = request.data.get('cards')
        if not isinstance(items, list):
            return Response({'detail': 'cards must be a list'},
                            status=status.HTTP_400_BAD_REQUEST)

        by_index = {rc.position_index: rc for rc in reading.cards.all()}
        touched = []
        for item in items:
            if not isinstance(item, dict):
                continue
            rc = by_index.get(item.get('position_index'))
            if rc is None:
                continue
            rc.x = self._clamp01(item.get('x'), rc.x)
            rc.y = self._clamp01(item.get('y'), rc.y)
            if 'is_reversed' in item:
                rc.is_reversed = bool(item['is_reversed'])
            touched.append(rc)
        if touched:
            ReadingCard.objects.bulk_update(touched, ['x', 'y', 'is_reversed'])

        reading = self.get_queryset().get(pk=reading.pk)
        return Response(ReadingSerializer(reading).data)

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

        # Question is optional — without one, the cards give a general reading.
        if hasattr(reading, 'interpretation'):
            return Response(
                InterpretationSerializer(reading.interpretation).data,
                status=status.HTTP_200_OK,
            )

        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

        # Anonymous users: enforce daily free limit before hitting the AI.
        if user is None:
            allowed, remaining = check_anon_daily_limit(request, kind='tarot')
            if not allowed:
                return Response(
                    {
                        'detail': 'rate_limited',
                        'message_ru': (
                            f'Ты уже использовал {ANON_DAILY_LIMIT} бесплатных интерпретации сегодня. '
                            'Войди или зарегистрируйся — это бесплатно.'
                        ),
                        'message_en': (
                            f"You've used all {ANON_DAILY_LIMIT} free interpretations for today. "
                            "Log in or sign up — it's free."
                        ),
                    },
                    status=429,
                )

        # Decide which tier (and therefore which model) to use.
        info = billing.tier_for(user)
        tier = info.tier
        model = ai_client.model_for_tier(tier)

        # Charge credits before generating, so over-quota free users get a clean 402.
        # The local model costs us no API tokens — it's free, so no credit charge.
        if not model.startswith('local:'):
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

    @action(detail=True, methods=['post'], url_path='interpret-stream')
    def interpret_stream(self, request: Request, pk=None):
        """Live (SSE) interpretation: streams the text token-by-token.

        Same gating/credits as ``interpret``, but returns text/event-stream:
          data: {"type":"delta","text":"..."}
          data: {"type":"done","interpretation":{...}}
          data: {"type":"error","detail":"..."}
        """
        reading = self.get_object()

        question = (request.data.get('question') or '').strip()
        if question and not hasattr(reading, 'interpretation'):
            reading.question = question
            reading.save(update_fields=['question'])

        if hasattr(reading, 'interpretation'):
            # Already generated — emit it as a single done event.
            data = InterpretationSerializer(reading.interpretation).data
            resp = StreamingHttpResponse(
                iter([_sse({'type': 'done', 'interpretation': data})]),
                content_type='text/event-stream',
            )
            resp['X-Accel-Buffering'] = 'no'
            resp['Cache-Control'] = 'no-cache'
            return resp

        # Question is optional — without one, the cards give a general reading.
        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

        if user is None:
            allowed, _ = check_anon_daily_limit(request, kind='tarot')
            if not allowed:
                return Response(
                    {'detail': 'rate_limited',
                     'message_ru': f'Ты уже использовал {ANON_DAILY_LIMIT} бесплатных интерпретации сегодня.',
                     'message_en': f"You've used all {ANON_DAILY_LIMIT} free interpretations for today."},
                    status=429,
                )

        tier = billing.tier_for(user).tier
        model = ai_client.model_for_tier(tier)
        # The local model costs us no API tokens — it's free, no credit charge.
        if not model.startswith('local:'):
            charged, balance = billing.charge_credits(
                user=user, kind=UsageLedger.KIND_AI_TAROT, model_used=model,
                reference_id=f'reading:{reading.pk}',
            )
            if not charged:
                return Response(
                    {'detail': 'out_of_credits',
                     'message_ru': 'Закончились бесплатные интерпретации. Оформи Premium или купи кредиты.',
                     'message_en': 'No credits left. Subscribe to Premium or buy a credit pack.',
                     'balance': balance},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

        base_prompt = ai_prompts.base_system(reading.locale)
        spread_prompt = ai_prompts.tarot_spread(reading.spread_type.slug, reading.locale)
        user_msg = _format_user_message(reading)

        def event_stream():
            try:
                final = None
                for kind, payload in ai_client.stream_interpretation(
                    base_system_prompt=base_prompt,
                    spread_system_prompt=spread_prompt,
                    user_message=user_msg,
                    model=model,
                    max_tokens=1800,
                    temperature=0.85,
                ):
                    if kind == 'delta':
                        yield _sse({'type': 'delta', 'text': payload})
                    else:
                        final = payload
                interpretation = Interpretation.objects.create(
                    reading=reading,
                    body_md=final.body,
                    model_used=final.model,
                    prompt_version=ai_prompts.PROMPT_VERSION,
                    token_count=final.input_tokens + final.output_tokens,
                )
                yield _sse({'type': 'done',
                            'interpretation': InterpretationSerializer(interpretation).data})
            except Exception as exc:  # noqa: BLE001 — surface as SSE error
                yield _sse({'type': 'error', 'detail': str(exc)[:200]})

        resp = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        resp['X-Accel-Buffering'] = 'no'   # tell nginx not to buffer the stream
        resp['Cache-Control'] = 'no-cache'
        return resp
