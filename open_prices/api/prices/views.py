from django.core.exceptions import FieldError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.prices.filters import PriceFilter
from open_prices.api.prices.serializers import (
    GroupedPriceStatsQuerySerializer,
    GroupedPriceStatsSerializer,
    PriceCreateSerializer,
    PriceFullSerializer,
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
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Price.objects.all()
    serializer_class = PriceFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PriceFilter
    ordering_fields = ["price", "date", "created"]
    ordering = ["created"]

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
        # get source
        source = get_source_from_request(self.request)
        # save
        price = serializer.save(
            owner=self.request.user.user_id, type=type, source=source
        )
        # return full price
        return Response(
            self.serializer_class(price).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(responses=PriceStatsSerializer, filters=True)
    @action(detail=False, methods=["GET"])
    def stats(self, request: Request) -> Response:
        qs = self.filter_queryset(self.get_queryset())
        return Response(qs.calculate_stats(), status=200)

    @extend_schema(
        request=GroupedPriceStatsQuerySerializer,
        responses=GroupedPriceStatsSerializer(many=True),
        filters=True,
        parameters=[
            OpenApiParameter(
                name="group_by",
                description="Field by which to group the statistics",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            )
        ],
    )
    @action(detail=False, methods=["GET"])
    def grouped_stats(self, request: Request) -> Response:
        qs = self.filter_queryset(self.get_queryset())

        # Validate and parse query parameters using the serializer
        serializer = GroupedPriceStatsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        group_by = serializer.validated_data.get("group_by")
        order_by = serializer.validated_data.get("order_by", None)

        try:
            data = qs.calculate_grouped_stats(group_by, order_by)
        except FieldError:
            return Response(
                {"detail": f"Invalid group_by field: {group_by}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply pagination
        paginator = self.paginator  # Use the default pagination class
        paginated_data = paginator.paginate_queryset(data, request, view=self)

        return paginator.get_paginated_response(paginated_data)
