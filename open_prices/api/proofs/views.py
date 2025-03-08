import PIL.Image
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django_q.tasks import async_task
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.proofs.filters import PriceTagFilter, ProofFilter
from open_prices.api.proofs.serializers import (
    PriceTagCreateSerializer,
    PriceTagFullSerializer,
    PriceTagUpdateSerializer,
    ProofCreateSerializer,
    ProofFullSerializer,
    ProofHalfFullSerializer,
    ProofProcessWithGeminiSerializer,
    ProofUpdateSerializer,
    ProofUploadSerializer,
)
from open_prices.api.utils import get_source_from_request
from open_prices.common.authentication import CustomAuthentication
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml import extract_from_price_tag
from open_prices.proofs.models import PriceTag, Proof
from open_prices.proofs.utils import store_file


class ProofViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = []  # see get_authenticators
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Proof.objects.all()
    serializer_class = ProofFullSerializer  # see get_serializer_class
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["date", "price_count", "created"]
    ordering = ["created"]

    def get_authenticators(self):
        if self.request and self.request.method in ["GET"]:
            # Note: we also allow anonymous upload ("POST")
            return super().get_authenticators()
        return [CustomAuthentication()]

    def get_queryset(self):
        queryset = self.queryset
        if self.request.method in ["GET"]:
            queryset = queryset.select_related("location")
            if self.action == "retrieve":
                queryset = queryset.prefetch_related("predictions")
        elif self.request.method in ["PATCH", "DELETE"]:
            # only return proofs owned by the current user
            if self.request.user.is_authenticated:
                queryset = queryset.filter(owner=self.request.user.user_id)
        return queryset

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
        permission_classes=[],  # allow anonymous upload
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
        # get owner & source
        owner = (
            self.request.user.user_id
            if self.request.user.is_authenticated
            else settings.ANONYMOUS_USER_ID
        )
        source = get_source_from_request(self.request)
        # save
        proof = serializer.save(owner=owner, source=source)
        # return the full proof
        return Response(ProofFullSerializer(proof).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=ProofProcessWithGeminiSerializer)
    @action(
        detail=False,
        methods=["POST"],
        url_path="process-with-gemini",
        parser_classes=[MultiPartParser],
    )
    def process_with_gemini(self, request: Request) -> Response:
        files = request.FILES.getlist("files")
        sample_files = [PIL.Image.open(file.file) for file in files]
        labels = [extract_from_price_tag(sample_file) for sample_file in sample_files]
        return Response({"labels": labels}, status=status.HTTP_200_OK)


class PriceTagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = []  # see get_authenticators
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = (
        PriceTag.objects.select_related("proof", "proof__location")
        .prefetch_related("predictions")
        .all()
    )
    serializer_class = PriceTagFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PriceTagFilter
    ordering_fields = ["proof_id", "created"]
    ordering = ["created"]

    def get_authenticators(self):
        if self.request and self.request.method in ["GET"]:
            return super().get_authenticators()
        return [CustomAuthentication()]

    def get_queryset(self):
        if self.action in ["create", "update"]:
            # We need to prefetch the price object if it exists to validate the
            # price_id field, and the proof object to validate the proof_id
            # field
            return (
                PriceTag.objects.select_related("proof").select_related("price").all()
            )
        return super().get_queryset()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PriceTagCreateSerializer
        elif self.request.method == "PATCH":
            return PriceTagUpdateSerializer
        return self.serializer_class

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        price_tag = self.get_object()
        if price_tag.price_id is not None:
            return Response(
                {"detail": "Cannot delete price tag with associated prices."},
                status=status.HTTP_403_FORBIDDEN,
            )
        price_tag.status = proof_constants.PriceTagStatus.deleted
        price_tag.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request: Request, *args, **kwargs):
        # validate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # save

        user_id = self.request.user.user_id
        price_tag = serializer.save(updated_by=user_id, created_by=user_id)

        if not settings.TESTING:
            async_task(
                "open_prices.proofs.ml.run_and_save_price_tag_extraction_from_id",
                price_tag.id,
            )

        # return full price tag
        return Response(
            self.serializer_class(price_tag).data, status=status.HTTP_201_CREATED
        )

    def update(self, request: Request, *args, **kwargs):
        # validate
        previous_price_tag: PriceTag = self.get_object()
        previous_bounding_box = previous_price_tag.bounding_box
        serializer = self.get_serializer(
            previous_price_tag, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        # save
        price_tag = serializer.save(updated_by=self.request.user.user_id)
        if (
            not settings.TESTING
            # Only run the extraction if the bounding box has changed
            and previous_bounding_box != price_tag.bounding_box
        ):
            async_task(
                "open_prices.proofs.ml.update_price_tag_extraction", price_tag.id
            )

        # return full price tag
        return Response(self.serializer_class(price_tag).data)
