from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.prices.filters import PriceFilter
from open_prices.api.prices.serializers import (
    PriceCreateSerializer,
    PriceFullSerializer,
)
from open_prices.common.authentication import CustomAuthentication
from open_prices.prices.models import Price


class PriceViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Price.objects.all()
    serializer_class = PriceFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PriceFilter
    ordering_fields = ["date", "created"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PriceCreateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user.user_id)

    def create(self, request: Request, *args, **kwargs):
        # validate & save
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        price = self.perform_create(serializer)
        # return full price
        return Response(
            self.serializer_class(price).data, status=status.HTTP_201_CREATED
        )
