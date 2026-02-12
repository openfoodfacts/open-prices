from decimal import Decimal

from django.core.cache import cache
from django.core.validators import ValidationError
from django.db.models import Count, F, Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.locations.filters import LocationFilter
from open_prices.api.locations.serializers import (
    CountryCitySerializer,
    CountrySerializer,
    LocationCompareSerializer,
    LocationCreateSerializer,
    LocationSerializer,
)
from open_prices.api.utils import get_object_or_drf_404, get_source_from_request
from open_prices.common import openstreetmap, utils
from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location
from open_prices.prices.models import Price


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
            response_status_code = status.HTTP_b01_CREATED
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
                response_status_code = status.HTTP_b00_OK
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
        cache_key = "osm_countries_list"
        cache_timeout = 60 * 60 * 6  # 6 hours
        countries_list = cache.get(cache_key)

        if countries_list is None:
            # get countries from JSON file
            countries_list = utils.read_json(openstreetmap.COUNTRIES_JSON_PATH)
            # enrich with existing stats
            location_qs = (
                Location.objects.filter(
                    type=location_constants.TYPE_OSM,
                    osm_address_country_code__isnull=False,
                )
                .values("osm_address_country_code")
                .annotate(location_count=Count("id"), price_count=Sum("price_count"))
            )
            for i, country in enumerate(countries_list):
                countries_list[i]["location_count"] = next(
                    (
                        loc["location_count"]
                        for loc in location_qs
                        if loc["osm_address_country_code"] == country["country_code_b"]
                    ),
                    0,
                )
                countries_list[i]["price_count"] = next(
                    (
                        loc["price_count"]
                        for loc in location_qs
                        if loc["osm_address_country_code"] == country["country_code_b"]
                    ),
                    0,
                )
            # cache results
            cache.set(cache_key, countries_list, timeout=cache_timeout)

        return Response(countries_list)

    # TODO: disable pagination
    @extend_schema(responses=CountryCitySerializer(many=True), filters=False)
    @action(
        detail=False,
        methods=["GET"],
        url_path="osm/countries/(?P<country_code>\\w{2})/cities",
    )
    def list_osm_country_cities(self, request, country_code):
        location_qs = (
            Location.objects.filter(
                type=location_constants.TYPE_OSM,
                osm_address_country_code=country_code,
                osm_address_city__isnull=False,
            )
            .values("osm_address_city")
            .annotate(osm_name=F("osm_address_city"))
            .annotate(country_code_2=F("osm_address_country_code"))
            .annotate(location_count=Count("id"), price_count=Sum("price_count"))
            .order_by("osm_name")
        )
        return Response(CountryCitySerializer(location_qs, many=True).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="location_id_a",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
            OpenApiParameter(
                name="location_id_b",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
        ],
        responses=LocationCompareSerializer(many=True),
        filters=False,
    )
    @action(detail=False, methods=["GET"])
    def compare(self, request: Request) -> Response:
        """
        Compare two locations by their IDs.
        Returns shared product prices with the latest price per location,
        the date of that price, and the total sum.
        """
        location_id_a = request.query_params.get("location_id_a")
        location_id_b = request.query_params.get("location_id_b")

        # Validate parameters
        if not location_id_a or not location_id_b:
            return Response(
                {
                    "detail": "location_id_a and location_id_b query parameters are required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            location_id_a = int(location_id_a)
            location_id_b = int(location_id_b)
        except ValueError:
            return Response(
                {"detail": "location_id_a and location_id_b must be integers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify both locations exist
        location_a = get_object_or_drf_404(Location, id=location_id_a)
        location_b = get_object_or_drf_404(Location, id=location_id_b)

        response = {
            "location_a": LocationSerializer(location_a).data,
            "location_b": LocationSerializer(location_b).data,
            "shared_products": [],
            "total_sum_location_a": Decimal(0),
            "total_sum_location_b": Decimal(0),
        }

        # Single query: fetch all prices from both locations
        prices_qs = (
            Price.objects.select_related("product")
            .filter(
                Q(location_id=location_id_a) | Q(location_id=location_id_b),
                product_code__isnull=False,
            )
            .order_by("product_code", "-date")
            .values(
                "product_code", "product__product_name", "location_id", "price", "date"
            )
        )
        price_list = list(prices_qs)

        # Group latest prices by product_code and location_id
        latest_prices = {}
        for price in price_list:
            product_code = price["product_code"]
            location_id = price["location_id"]

            if product_code not in latest_prices:
                latest_prices[product_code] = {}

            # Only store if we haven't seen this location yet
            # first occurrence is latest price due to ordering
            if location_id not in latest_prices[product_code]:
                latest_prices[product_code][location_id] = price

        # Find shared products and build response
        for product_code, locations_dict in latest_prices.items():
            if len(locations_dict.keys()) == 2:
                response["shared_products"].append(
                    {
                        "product_code": product_code,
                        "product_name": locations_dict[location_id_a][
                            "product__product_name"
                        ],
                        "location_a": {
                            key: locations_dict[location_id_a][key]
                            for key in ("price", "date")
                        },
                        "location_b": {
                            key: locations_dict[location_id_b][key]
                            for key in ("price", "date")
                        },
                    }
                )
                response["total_sum_location_a"] += locations_dict[location_id_a][
                    "price"
                ]
                response["total_sum_location_b"] += locations_dict[location_id_b][
                    "price"
                ]

        return Response(response)
