from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.products.filters import ProductFilter
from open_prices.api.products.serializers import ProductFullSerializer
from open_prices.api.utils import get_object_or_drf_404
from open_prices.common.openfoodfacts import (
    update_off_product,
    update_off_product_image,
)
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

    @action(
        detail=False, methods=["PATCH", "POST"], url_path=r"off_update/(?P<code>.+)"
    )
    def update_off_product(self, request: Request, code):
        result = update_off_product(
            code,
            flavor=request.data.get("flavor", "off"),
            update_params=request.data.get("update_params"),
        )
        if result:
            return Response(result, status=200)
        return Response(status=400)

    @action(
        detail=False,
        methods=["PATCH", "POST"],
        url_path=r"off_update_image/(?P<code>.+)",
    )
    def update_off_product_image(self, request: Request, code):
        result = update_off_product_image(
            code,
            flavor=request.data.get("flavor", "off"),
            image_src=request.data.get("image_src"),
        )
        if result:
            return Response(result, status=200)
        return Response(status=400)
