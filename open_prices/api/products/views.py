from django_filters.rest_framework import DjangoFilterBackend
from openfoodfacts.barcode import normalize_barcode
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.products.filters import ProductFilter
from open_prices.api.products.serializers import (
    ProductFullSerializer,
    ProductOffUpdateRequestSerializer,
    ProductOffUploadImageRequestSerializer,
)
from open_prices.api.utils import get_object_or_drf_404
from open_prices.common.authentication import CustomAuthentication
from open_prices.common.openfoodfacts import (
    create_or_update_product_in_off,
    upload_product_image_in_off,
)
from open_prices.products.models import Product


class ProductViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = []  # see get_authenticators
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = (
        Product.OFF_SCORE_FIELDS + Product.COUNT_FIELDS + ["id", "created"]
    )
    ordering = ["id"]

    def get_authenticators(self):
        if self.request and self.request.method in ["GET"]:
            return super().get_authenticators()
        return [CustomAuthentication()]

    @action(detail=False, methods=["GET"], url_path=r"code/(?P<code>\d+)")
    def get_by_code(self, request: Request, code):
        code = normalize_barcode(code)
        product = get_object_or_drf_404(Product, code=code)
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["PATCH"],
        url_path=r"code/(?P<code>\d+)/off-update",
    )
    def create_or_update_in_off(self, request: Request, code):
        serializer = ProductOffUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = create_or_update_product_in_off(
            code,
            flavor=serializer.validated_data["flavor"],
            country_code=serializer.validated_data["product_language_code"],
            owner=self.request.user.user_id,
            update_params=serializer.validated_data["update_params"],
        )
        if result:
            return Response(result, status=200)
        return Response(status=400)

    @action(
        detail=False,
        methods=["PATCH"],
        url_path=r"code/(?P<code>\d+)/off-upload-image",
    )
    def upload_image_in_off(self, request: Request, code):
        serializer = ProductOffUploadImageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_language_code = serializer.validated_data["product_language_code"]
        result = upload_product_image_in_off(
            code,
            flavor=serializer.validated_data["flavor"],
            country_code=product_language_code,
            image_data_base64=serializer.validated_data["image_data_base64"],
            selected={"front": {product_language_code: {}}},
        )
        if result:
            return Response(result, status=200)
        return Response(status=400)
