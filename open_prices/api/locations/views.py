from django.core.validators import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.locations.filters import LocationFilter
from open_prices.api.locations.serializers import (
    CountrySerializer,
    LocationCreateSerializer,
    LocationSerializer,
)
from open_prices.api.utils import get_object_or_drf_404, get_source_from_request
from open_prices.common import openstreetmap, utils
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
    ordering_fields = ["id", "created"] + Location.COUNT_FIELDS
    ordering = ["id"]

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
            response_data = self.serializer_class(location).data
            response_status_code = status.HTTP_201_CREATED
        # avoid duplicates: return existing location instead
        except ValidationError as e:
            if any(
                constraint_name in e.messages[0]
                for constraint_name in location_constants.UNIQUE_CONSTRAINT_NAME_LIST
            ):
                location = Location.objects.get(**serializer.validated_data)
                response_data = {
                    **self.serializer_class(location).data,
                    "detail": "duplicate",
                }
                response_status_code = status.HTTP_200_OK
        return Response(response_data, status=response_status_code)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="osm_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                enum=location_constants.OSM_TYPE_LIST,
                required=True,
            ),
            OpenApiParameter(
                name="osm_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    )
    @action(
        detail=False, methods=["GET"], url_path=r"osm/(?P<osm_type>\w+)/(?P<osm_id>\d+)"
    )
    def get_by_osm(self, request, osm_type, osm_id):
        location = get_object_or_drf_404(Location, osm_type=osm_type, osm_id=osm_id)
        serializer = self.get_serializer(location)
        return Response(serializer.data)

    # TODO: disable pagination
    @extend_schema(responses=CountrySerializer(many=True), filters=False)
    @action(detail=False, methods=["GET"], url_path="osm/countries")
    def list_osm_countries(self, request):
        countries = utils.read_json(openstreetmap.COUNTRIES_JSON_PATH)
        # TODO: enrich with price_count & location_count
        # TODO: cache results
        return Response(countries)
