from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.proofs.filters import ProofFilter
from open_prices.api.proofs.serializers import (
    ProofCreateSerializer,
    ProofFullSerializer,
    ProofUpdateSerializer,
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
    # parser_classes = [FormParser, MultiPartParser]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Proof.objects.none()
    serializer_class = ProofFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["price_count", "date", "created"]

    def get_queryset(self):
        # only return proofs owned by the current user
        if self.request.user.is_authenticated:
            return Proof.objects.filter(owner=self.request.user.user_id)
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ProofUpdateSerializer
        return self.serializer_class

    @action(detail=False, methods=["POST"], url_path="upload")
    @parser_classes([FormParser, MultiPartParser])
    def upload(self, request: Request) -> Response:
        # build proof
        if not request.data.get("file"):
            return Response(
                {"file": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_path, mimetype = store_file(request.data.get("file"))
        proof_create_data = {
            "file_path": file_path,
            "mimetype": mimetype,
            **{key: request.data.get(key) for key in Proof.CREATE_FIELDS},
        }
        # validate
        serializer = ProofCreateSerializer(data=proof_create_data)
        serializer.is_valid(raise_exception=True)
        # get source
        self.source = self.request.GET.get("app_name", "API")
        # save
        proof = serializer.save(owner=self.request.user.user_id, source=self.source)
        # return full proof
        return Response(ProofFullSerializer(proof).data, status=status.HTTP_201_CREATED)
