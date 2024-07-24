from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from open_prices.api.prices.filters import PriceFilter
from open_prices.api.prices.serializers import PriceFullSerializer
from open_prices.prices.models import Price


class PriceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PriceFilter
    ordering_fields = ["date", "created"]
