from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from open_prices.api.products.filters import ProductFilter
from open_prices.api.products.serializers import ProductSerializer
from open_prices.products.models import Product


class ProductViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ["price_count"]

    @action(detail=False, methods=["GET"], url_path=r"code/(?P<code>\d+)")
    def get_product_by_code(self, request, code):
        product = get_object_or_404(Product, code=code)
        serializer = self.get_serializer(product)
        return Response(serializer.data)
