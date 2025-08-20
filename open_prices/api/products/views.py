from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.products.filters import ProductFilter
from open_prices.api.products.serializers import ProductFullSerializer
from open_prices.api.utils import get_object_or_drf_404
from open_prices.products.models import Product


class ProductViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Product.objects.all()
    serializer_class = ProductFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = (
        Product.OFF_SCORE_FIELDS + Product.COUNT_FIELDS + ["id", "created"]
    )
    ordering = ["id"]

    @action(detail=False, methods=["GET"], url_path=r"code/(?P<code>\d+)")
    def get_by_code(self, request: Request, code):
        product = get_object_or_drf_404(Product, code=code)
        serializer = self.get_serializer(product)
        return Response(serializer.data)
