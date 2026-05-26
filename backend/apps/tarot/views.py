"""Views for tarot domain — cards and spread types."""
from rest_framework import mixins, viewsets
from rest_framework.exceptions import NotFound

from apps.tarot.models import Card, SpreadType
from apps.tarot.serializers import CardSerializer, SpreadTypeSerializer


class CardViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /api/v1/cards/          — list all cards
    GET /api/v1/cards/?suit=... — filter by suit
    """

    serializer_class = CardSerializer
    permission_classes = []
    authentication_classes = []

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
