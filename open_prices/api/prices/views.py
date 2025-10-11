from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.prices.filters import PriceFilter
from open_prices.api.prices.serializers import (
    PriceCreateSerializer,
    PriceFullSerializer,
    PriceHistorySerializer,
    PriceStatsSerializer,
    PriceUpdateSerializer,
)
from open_prices.api.utils import get_source_from_request
from open_prices.common.authentication import CustomAuthentication
from open_prices.prices import constants as price_constants
from open_prices.prices.models import Price


class PriceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = []  # see get_authenticators
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Price.objects.all()
    serializer_class = PriceFullSerializer  # see get_serializer_class
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PriceFilter
    ordering_fields = ["id", "price", "date", "created"]
    ordering = ["id"]

    def get_authenticators(self):
        if self.request and self.request.method in ["GET"]:
            return super().get_authenticators()
        return [CustomAuthentication()]

    def get_queryset(self):
        if self.request.method in ["GET"]:
            return self.queryset.select_related("product", "location", "proof")
        elif self.request.method in ["PATCH", "DELETE"]:
            # only return prices owned by the current user
            if self.request.user.is_authenticated:
                return self.queryset.filter(owner=self.request.user.user_id)
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PriceCreateSerializer
        elif self.request.method == "PATCH":
            return PriceUpdateSerializer
        return self.serializer_class

    def create(self, request: Request, *args, **kwargs):
        # validate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get type
        type = serializer.validated_data.get("type") or (
            price_constants.TYPE_PRODUCT
            if serializer.validated_data.get("product_code")
            else price_constants.TYPE_CATEGORY
        )
        # get owner
        owner = self.request.user.user_id
        # get source
        source = get_source_from_request(self.request)
        # save
        price = serializer.save(type=type, owner=owner, source=source)
        # return full price
        return Response(
            self.serializer_class(price).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(responses=PriceStatsSerializer, filters=True)
    @action(detail=False, methods=["GET"])
    def stats(self, request: Request) -> Response:
        qs = self.filter_queryset(self.get_queryset())
        return Response(qs.calculate_stats(), status=200)

    @extend_schema(responses=PriceHistorySerializer(many=True))
    @action(detail=True, methods=["GET"])
    def history(self, request: Request, pk=None) -> Response:
        price = self.get_object()
        return Response(price.get_history_list(), status=200)
