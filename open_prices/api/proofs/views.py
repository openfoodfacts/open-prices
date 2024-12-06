import PIL.Image
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.proofs.filters import ProofFilter
from open_prices.api.proofs.serializers import (
    ProofCreateSerializer,
    ProofFullSerializer,
    ProofHalfFullSerializer,
    ProofProcessWithGeminiSerializer,
    ProofUpdateSerializer,
    ProofUploadSerializer,
)
from open_prices.api.utils import get_source_from_request
from open_prices.common.authentication import CustomAuthentication
from open_prices.common.gemini import handle_bulk_labels
from open_prices.proofs.models import Proof
from open_prices.proofs.utils import store_file


class ProofPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ("retrieve", "list"):
            # Allow any user (even anonymous) to view any proof
            return True
        elif request.method == "POST" and request.path.startswith(
            "/api/v1/proofs/upload"
        ):
            # Allow anonymous users to upload proofs
            return True

        # Require authenticated user for the rest ("destroy", "update",
        # Gemini proof processing)
        return request.user and request.user.is_authenticated


class ProofViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [ProofPermission]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Proof.objects.all()
    serializer_class = ProofFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["date", "price_count", "created"]
    ordering = ["created"]

    def get_queryset(self):
        if self.request.method in ["GET"]:
            # Select all proofs along with their locations using a select
            # related query (1 single query)
            # Then prefetch all the predictions related to the proof using
            # a prefetch related query (only 1 query for all proofs)
            return self.queryset.select_related("location").prefetch_related(
                "predictions"
            )
        elif self.request.method in ["PATCH", "DELETE"]:
            if self.request.user.is_moderator:
                return self.queryset
            # for patch and delete actions, only return proofs owned by the
            # current user if not a moderator
            return self.queryset.filter(owner=self.request.user.user_id)

        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ProofUpdateSerializer
        elif self.action == "list":
            return ProofHalfFullSerializer
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
        source = get_source_from_request(self.request)
        # Here, user is either a `open_prices.users.models.User` (if
        # authenticated) or an `django.contrib.auth.models.AnonymousUser`
        # (if not authenticated)
        user = self.request.user
        owner = None if user.is_anonymous else user.user_id
        # save
        proof = serializer.save(owner=owner, source=source, anonymous=user.is_anonymous)
        # return full proof
        return Response(ProofFullSerializer(proof).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=ProofProcessWithGeminiSerializer)
    @action(
        detail=False,
        methods=["POST"],
        url_path="process_with_gemini",
        parser_classes=[MultiPartParser],
    )
    def process_with_gemini(self, request: Request) -> Response:
        files = request.FILES.getlist("files")
        sample_files = [PIL.Image.open(file.file) for file in files]
        res = handle_bulk_labels(sample_files)
        return Response(res, status=status.HTTP_200_OK)
