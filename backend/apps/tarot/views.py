"""Views for tarot domain — cards and spread types."""
import hashlib
from datetime import date

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.tarot.models import Card, SpreadType
from apps.tarot.serializers import CardSerializer, SpreadTypeSerializer


def _daily_card_for(seed: str, count: int) -> tuple[int, bool]:
    """Deterministic (index, is_reversed) from seed string."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "big") % count
    is_reversed = digest[4] & 1 == 1
    return idx, is_reversed


class CardViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /api/v1/cards/          — list all cards
    GET /api/v1/cards/?suit=... — filter by suit
    GET /api/v1/cards/daily/    — daily card (one per day per user)
    """

    serializer_class = CardSerializer
    permission_classes = [AllowAny]
    # authentication_classes intentionally left as DRF default so JWT works
    # opportunistically — anonymous requests still pass thanks to AllowAny.

    VALID_SUITS = {'major', 'cups', 'wands', 'swords', 'pentacles'}

    def get_queryset(self):
        qs = Card.objects.all()
        suit = self.request.query_params.get('suit')
        if suit is not None:
            if suit not in self.VALID_SUITS:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    {'suit': f"Invalid suit '{suit}'. Choose from: {', '.join(sorted(self.VALID_SUITS))}."}
                )
            qs = qs.filter(suit=suit)
        return qs

    @action(detail=False, methods=['get'], url_path='daily', permission_classes=[AllowAny])
    def daily(self, request: Request) -> Response:
        """Return a deterministic card-of-the-day for the current user (or anon)."""
        cards = list(Card.objects.all().order_by('id'))
        if not cards:
            raise NotFound("No cards in deck.")

        # Per-user, per-day deterministic seed. Falls back to client IP for anon.
        if request.user and request.user.is_authenticated:
            who = f"user:{request.user.pk}"
        else:
            # Anonymous: same card for all anon users on the same day.
            who = "anon"

        seed = f"{date.today().isoformat()}|{who}"
        idx, is_reversed = _daily_card_for(seed, len(cards))
        card = cards[idx]

        return Response({
            'date': date.today().isoformat(),
            'card': CardSerializer(card).data,
            'is_reversed': is_reversed,
        })


class SpreadTypeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET /api/v1/spreads/{slug}/  — retrieve a spread type by slug
    """

    serializer_class = SpreadTypeSerializer
    permission_classes = []
    authentication_classes = []
    lookup_field = 'slug'

    def get_queryset(self):
        return SpreadType.objects.all()

    def get_object(self):
        slug = self.kwargs['slug']
        try:
            return SpreadType.objects.get(slug=slug)
        except SpreadType.DoesNotExist:
            raise NotFound(detail=f"Spread '{slug}' not found.")
