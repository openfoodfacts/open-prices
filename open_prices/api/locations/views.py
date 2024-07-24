from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from open_prices.api.locations.filters import LocationFilter
from open_prices.api.locations.serializers import LocationSerializer
from open_prices.locations.models import Location


class LocationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LocationFilter
    ordering_fields = ["price_count"]
