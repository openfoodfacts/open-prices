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
from open_prices.locations.models import Location


class LocationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = []
    permission_classes = []
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
        # before save: check if location already exists. If so, return it
        try:
            location = Location.objects.get(**serializer.validated_data)
            return Response(
                self.serializer_class(location).data, status=status.HTTP_200_OK
            )
        except Location.DoesNotExist:
            pass
        # save
        location = serializer.save(source=source)
        # return full location
        return Response(
            self.serializer_class(location).data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=False, methods=["GET"], url_path=r"osm/(?P<osm_type>\w+)/(?P<osm_id>\d+)"
    )
    def get_by_osm(self, request, osm_type, osm_id):
        location = get_object_or_drf_404(Location, osm_type=osm_type, osm_id=osm_id)
        serializer = self.get_serializer(location)
        return Response(serializer.data)
