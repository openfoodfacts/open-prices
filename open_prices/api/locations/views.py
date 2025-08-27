from django.core.validators import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.locations.filters import LocationFilter
from open_prices.api.locations.serializers import (
    LocationCreateSerializer,
    LocationSerializer,
)
from open_prices.api.utils import get_object_or_drf_404, get_source_from_request
from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location


class LocationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LocationFilter
    ordering_fields = Location.COUNT_FIELDS + ["created"]
    ordering = ["created"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LocationCreateSerializer
        return self.serializer_class

    def create(self, request: Request, *args, **kwargs):
        # validate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get source
        source = get_source_from_request(self.request)
        # save
        try:
            location = serializer.save(source=source)
            response_status = status.HTTP_201_CREATED
        # avoid duplicates: return existing location instead
        except ValidationError as e:
            if any(
                constraint_name in e.messages[0]
                for constraint_name in location_constants.UNIQUE_CONSTRAINT_NAME_LIST
            ):
                location = Location.objects.get(**serializer.validated_data)
                response_status = status.HTTP_200_OK
        return Response(self.serializer_class(location).data, status=response_status)

    @action(
        detail=False, methods=["GET"], url_path=r"osm/(?P<osm_type>\w+)/(?P<osm_id>\d+)"
    )
    def get_by_osm(self, request, osm_type, osm_id):
        location = get_object_or_drf_404(Location, osm_type=osm_type, osm_id=osm_id)
        serializer = self.get_serializer(location)
        return Response(serializer.data)
