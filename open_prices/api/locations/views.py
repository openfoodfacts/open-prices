from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from open_prices.api.locations.filters import LocationFilter
from open_prices.api.locations.serializers import LocationFullSerializer
from open_prices.locations.models import Location


class LocationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Location.objects.all()
    serializer_class = LocationFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LocationFilter
    ordering_fields = ["price_count"]

    @action(
        detail=False, methods=["GET"], url_path=r"osm/(?P<osm_type>\w+)/(?P<osm_id>\d+)"
    )
    def get_location_by_osm(self, request, osm_type, osm_id):
        location = get_object_or_404(Location, osm_type=osm_type, osm_id=osm_id)
        serializer = self.get_serializer(location)
        return Response(serializer.data)
