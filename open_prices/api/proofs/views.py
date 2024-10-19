from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.proofs.filters import ProofFilter
from open_prices.api.proofs.serializers import (
    ProofCreateSerializer,
    ProofFullSerializer,
    ProofUpdateSerializer,
    ProofUploadSerializer,
)
from open_prices.common.authentication import CustomAuthentication
from open_prices.proofs.models import Proof
from open_prices.proofs.utils import store_file


class ProofViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Proof.objects.none()
    serializer_class = ProofFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["date", "price_count", "created"]
    ordering = ["created"]

    def get_queryset(self):
        # only return proofs owned by the current user
        if self.request.user.is_authenticated:
            queryset = Proof.objects.filter(owner=self.request.user.user_id)
            if self.request.method in ["GET"]:
                return queryset.select_related("location")
            return queryset
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ProofUpdateSerializer
        return self.serializer_class

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        proof = self.get_object()
        if proof.prices.count():
            return Response(
                {"detail": "Cannot delete proof with associated prices"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @extend_schema(request=ProofUploadSerializer, responses=ProofFullSerializer)
    @action(
        detail=False,
        methods=["POST"],
        url_path="upload",
        parser_classes=[MultiPartParser],
    )
    def upload(self, request: Request) -> Response:
        # build proof
        if not request.data.get("file"):
            return Response(
                {"file": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_path, mimetype, image_thumb_path = store_file(request.data.get("file"))
        proof_create_data = {
            "file_path": file_path,
            "mimetype": mimetype,
            "image_thumb_path": image_thumb_path,
            **{
                key: request.data.get(key)
                for key in Proof.CREATE_FIELDS
                if key in request.data
            },
        }
        # validate
        serializer = ProofCreateSerializer(data=proof_create_data)
        serializer.is_valid(raise_exception=True)
        # get source
        self.source = self.request.GET.get("app_name", "API")
        # save
        proof = serializer.save(
            owner=self.request.user.user_id,
            source=self.source,
        )
        # return full proof
        return Response(ProofFullSerializer(proof).data, status=status.HTTP_201_CREATED)
