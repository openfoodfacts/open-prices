import re

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

from open_prices.api.proofs.filters import (
    PriceTagFilter,
    ProofFilter,
    ReceiptItemFilter,
)
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
    ReceiptItemFullSerializer,
)
from open_prices.api.utils import get_source_from_request
from open_prices.common.authentication import CustomAuthentication
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml import extract_from_price_tag
from open_prices.proofs.models import PriceTag, Proof, ReceiptItem
from open_prices.proofs.utils import compute_file_md5, store_file


def is_smoothie_app_version_4_20(source: str | None) -> bool:
    """Return True if the requests comes from Smoothie app version 4.20.

    This is used to detect the Smoothie app version 4.20 which has a bug
    where it sets the `ready_for_price_tag_validation` flag to True when
    uploading price tag proofs, even when it should not be set.
    """
    if source and (
        match := re.search(r"^Smoothie - OpenFoodFacts \((\d+)\.(\d+)\.(\d+)", source)
    ):
        # source is in the format
        # "Smoothie - OpenFoodFacts (4.18.1+1434)...""
        smoothie_major = int(match.group(1))
        smoothie_minor = int(match.group(2))

        return smoothie_major == 4 and smoothie_minor == 20

    return False


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
        # NOTE: image will be stored even if the proof serializer fails...
        file = request.data.get("file")
        file_path, mimetype, image_thumb_path = store_file(file)
        md5_hash = compute_file_md5(file)
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

        # We check if a proof with the same MD5 hash already exists,
        # uploaded by the same user, with the same type, location and date.
        # If yes, we return it instead of creating a new one
        duplicate_proof = Proof.objects.filter(
            md5_hash=md5_hash,
            owner=owner,
            type=serializer.validated_data["type"],
            # location OSM id/type can be null (for online stores)
            location_osm_id=serializer.validated_data.get("location_osm_id"),
            location_osm_type=serializer.validated_data.get("location_osm_type"),
            date=serializer.validated_data["date"],
        ).first()

        if duplicate_proof:
            # We remove the uploaded file as it's a duplicate
            (settings.IMAGES_DIR / file_path).unlink(missing_ok=True)

            return Response(
                ProofFullSerializer(duplicate_proof).data,
                status=status.HTTP_200_OK,
            )

        source = get_source_from_request(self.request)
        save_kwargs = {
            "source": source,
            "owner": owner,
            "md5_hash": md5_hash,
        }
        # Smoothie sets incorrectly the ready_for_price_tag_validation flag
        # when uploading price tag proofs on version 4.20.
        # This should only be set to True for multiple proof upload.
        # It was fixed in the upcoming release of Smoothie 4.21
        # (see https://github.com/openfoodfacts/smooth-app/pull/6794)
        if is_smoothie_app_version_4_20(source):
            save_kwargs["ready_for_price_tag_validation"] = False

        # save
        proof = serializer.save(**save_kwargs)
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
        labels = [
            extract_from_price_tag(sample_file).parsed.model_dump()
            for sample_file in sample_files
        ]
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


class ReceiptItemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ReceiptItem.objects.all()
    serializer_class = ReceiptItemFullSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReceiptItemFilter
    ordering_fields = ["proof_id", "created", "order"]
    ordering = ["order"]

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
                ReceiptItem.objects.select_related("proof")
                .select_related("price")
                .all()
            )
        return super().get_queryset()

    def create(self, request: Request, *args, **kwargs):
        # validate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # save

        receipt_item = serializer.save()

        # return full price tag
        return Response(
            self.serializer_class(receipt_item).data, status=status.HTTP_201_CREATED
        )
