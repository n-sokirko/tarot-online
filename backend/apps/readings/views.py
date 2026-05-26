"""Views for reading sessions."""
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from apps.readings.models import Reading
from apps.readings.serializers import CreateReadingSerializer, ReadingSerializer


class ReadingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST /api/v1/readings/       — create a new reading
    GET  /api/v1/readings/{id}/  — retrieve a reading by id
    """

    permission_classes = []
    authentication_classes = []

    def get_queryset(self):
        return Reading.objects.select_related('spread_type').prefetch_related(
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

        # Re-fetch with all relations for the response
        reading = (
            Reading.objects.select_related('spread_type')
            .prefetch_related('cards', 'cards__card')
            .get(pk=reading.pk)
        )
        output = ReadingSerializer(reading)
        return Response(output.data, status=status.HTTP_201_CREATED)
