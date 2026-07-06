from pathlib import Path

import PIL.Image
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django_q.tasks import async_task
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.moderation.serializers import FlagCreateSerializer, FlagSerializer
from open_prices.api.proofs.filters import (
    PriceTagFilter,
    ProofFilter,
    ReceiptItemFilter,
)
from open_prices.api.proofs.serializers import (
    DraftProofAnonymizeRequestSerializer,
    PriceTagCreateSerializer,
    PriceTagFullSerializer,
    PriceTagUpdateSerializer,
    ProofCreateSerializer,
    ProofDraftUploadSerializer,
    ProofFullSerializer,
    ProofHalfFullSerializer,
    ProofHistorySerializer,
    ProofProcessWithGeminiSerializer,
    ProofUpdateSerializer,
    ProofUploadSerializer,
    ReceiptItemFullSerializer,
)
from open_prices.api.utils import get_source_from_request
from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.common.authentication import (
    CustomAuthentication,
    has_token_from_cookie_or_header,
)
from open_prices.common.permission import (
    OnlyObjectOwnerIsAllowedReadWrite,
    OnlyObjectOwnerOrModeratorIsAllowedWrite,
)
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.constants import TYPE_RECEIPT
from open_prices.proofs.ml.price_tags import extract_from_price_tag
from open_prices.proofs.models import PriceTag, Proof, ReceiptItem
from open_prices.proofs.utils import (
    compute_file_md5,
    save_anonymized_receipt,
    store_file,
)


def base_upload(request: Request, draft: bool = False) -> Response:
    # build proof
    file = request.data.get("file")
    if not file:
        return Response(
            {"file": ["This field is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # NOTE: image will be stored even if the proof serializer fails...
    file_path, mimetype, image_thumb_path = store_file(file)
    image_md5_hash = compute_file_md5(file)
    proof_create_data = {
        "file_path": file_path,
        "mimetype": mimetype,
        "image_thumb_path": image_thumb_path,
        "draft": draft,
        **{
            key: request.data.get(key)
            for key in Proof.CREATE_FIELDS
            if key in request.data
        },
    }
    # validate
    serializer = ProofCreateSerializer(data=proof_create_data)
    serializer.is_valid(raise_exception=True)

    # get owner (we allow anonymous upload, only if token is not present)
    if request.user.is_authenticated:
        owner = request.user.user_id
    else:
        if draft:
            # It's not possible to upload a draft proof anonymously, as the user needs to be able to finalize it later
            return Response(
                {
                    "detail": "Authentication is required to upload a draft proof. Please pass a valid token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if has_token_from_cookie_or_header(request):
            return Response(
                {
                    "detail": "Authentication failed. Please pass a valid token, or remove it to upload the proof anonymously."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            owner = settings.ANONYMOUS_USER_ID

    # get source
    source = get_source_from_request(request)

    # We check if a proof with the same MD5 hash already exists,
    # uploaded by the same user, with the same type, location and date.
    # If yes, we return it instead of creating a new one
    duplicate_proof = Proof.objects.filter(
        image_md5_hash=image_md5_hash,
        owner=owner,
        type=serializer.validated_data.get("type"),
        # location OSM id/type can be null (for online stores)
        location_osm_id=serializer.validated_data.get("location_osm_id"),
        location_osm_type=serializer.validated_data.get("location_osm_type"),
        date=serializer.validated_data.get("date"),
    ).first()
    if duplicate_proof:
        # We remove the uploaded file as it's a duplicate
        (settings.IMAGES_DIR / file_path).unlink(missing_ok=True)
        response_status_code = status.HTTP_200_OK
        # see note in common/openfoodfacts.py
        if common_openfoodfacts.is_smoothie_app_version_leq_4_20(source):
            response_status_code = status.HTTP_201_CREATED

        return Response(
            {**ProofFullSerializer(duplicate_proof).data, "detail": "duplicate"},
            status=response_status_code,
        )

    save_kwargs = {
        "owner": owner,
        "image_md5_hash": image_md5_hash,
        "source": source,
    }
    # see note in common/openfoodfacts.py
    if common_openfoodfacts.is_smoothie_app_version_4_20(source):
        save_kwargs["ready_for_price_tag_validation"] = False
    # save
    proof = serializer.save(**save_kwargs)
    # return full proof
    return Response(ProofFullSerializer(proof).data, status=status.HTTP_201_CREATED)


class ProofViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = []  # see get_authenticators
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        OnlyObjectOwnerOrModeratorIsAllowedWrite,  # for edit & delete
    ]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Proof.objects.all()  # proofs are already filtered out
    serializer_class = ProofFullSerializer  # see get_serializer_class
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["id", "date", "price_count", "created"]
    ordering = ["id"]

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
        return base_upload(request, draft=False)

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

    @extend_schema(responses=ProofHistorySerializer(many=True))
    @action(detail=True, methods=["GET"])
    def history(self, request: Request, pk=None) -> Response:
        proof = self.get_object()
        return Response(proof.get_history_list(), status=200)

    @extend_schema(
        request=FlagCreateSerializer, responses=FlagSerializer, tags=["moderation"]
    )
    @action(detail=True, methods=["POST"])
    def flag(self, request: Request, pk=None) -> Response:
        proof = self.get_object()
        serializer = FlagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get owner
        owner = self.request.user.user_id
        # get source
        source = get_source_from_request(self.request)
        # save
        flag = serializer.save(content_object=proof, owner=owner, source=source)
        return Response(FlagSerializer(flag).data, status=status.HTTP_201_CREATED)


class ProofDraftViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [
        IsAuthenticated,
        OnlyObjectOwnerIsAllowedReadWrite,
    ]
    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
    ]  # disable "put" (full update)
    queryset = Proof.all_objects.is_draft().all()  # only draft proofs
    serializer_class = ProofFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["id", "date", "created"]
    ordering = ["id"]

    def get_queryset(self):
        queryset = self.queryset
        # Only keep draft proofs owned by the user
        user_id = self.request.user.user_id
        queryset = queryset.filter(owner=user_id)
        if self.request.method in ["GET"] and self.action == "retrieve":
            queryset = queryset.prefetch_related("predictions")
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=ProofDraftUploadSerializer, responses=ProofFullSerializer)
    @action(
        detail=False,
        methods=["POST"],
        url_path="upload",
        parser_classes=[MultiPartParser],
    )
    def upload(self, request: Request) -> Response:
        """Upload a draft proof.

        Only the file and type fields are expected. ML models runs immediately asynchronously."""
        return base_upload(request, draft=True)

    @extend_schema(
        request=DraftProofAnonymizeRequestSerializer, responses=ProofFullSerializer
    )
    @action(
        detail=True,
        methods=["POST"],
        url_path="anonymize",
    )
    def anonymize_receipt(self, request: Request, pk=None) -> Response:
        """Anonymize a receipt."""
        proof = self.get_object()

        # No need to check that this is a draft proof, as the queryset filter ensures it
        if proof.type != TYPE_RECEIPT:
            return Response(
                {"detail": "Only receipts can be anonymized"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Warning: bounding boxes here have the same format [x_min, y_min, x_max, y_max]
        # as the `Word` bounding boxes in the OCR results.
        # Currently, the format used by the bounding boxes of price tags use a different
        # format ([y_min, x_min, y_max, x_max]).
        # The [x_min, y_min, x_max, y_max] format is much more common, and we should migrate
        # price tag bounding boxes to that format in the future for consistency.
        serializer = DraftProofAnonymizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_path = Path(proof.file_path)
        image_thumb_path = Path(proof.image_thumb_path)
        # Redact the personal information from the image by drawing black boxes over
        # the bounding boxes, and save the new image and thumbnail to the filesystem.
        # We don't update the image hash, so that the proof duplication detection
        # still works.
        new_image_path, new_image_thumb_path = save_anonymized_receipt(
            image_path=image_path,
            image_thumb_path=image_thumb_path,
            bounding_boxes=serializer.data["bounding_boxes"],
        )

        if new_image_path != image_path or new_image_thumb_path != image_thumb_path:
            proof.file_path = str(new_image_path)
            proof.image_thumb_path = str(new_image_thumb_path)
            proof._change_reason = "Saving new image path after anonymization"
            proof.save()

        return Response(ProofFullSerializer(proof).data, status=status.HTTP_200_OK)

    @extend_schema(request=ProofUpdateSerializer, responses=ProofFullSerializer)
    def partial_update(self, request: Request, pk=None) -> Response:
        """Finalize a draft proof - set draft=False and add full metadata."""
        proof = self.get_object()
        # Validate required fields
        serializer = self.get_serializer(proof, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Update fields
        for field in Proof.UPDATE_FIELDS:
            if field in serializer.validated_data:
                setattr(proof, field, serializer.validated_data[field])

        # Check required fields for finalization
        missing_fields = []
        if not proof.date:
            missing_fields.append("date")
        if not proof.currency:
            missing_fields.append("currency")

        if missing_fields:
            return Response(
                {"detail": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proof.draft = False
        proof._change_reason = "Finalize draft proof"
        proof.save()

        return Response(ProofFullSerializer(proof).data, status=status.HTTP_200_OK)


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
    ordering_fields = ["id", "proof_id", "status", "created"]
    ordering = ["id"]

    def get_authenticators(self):
        if self.request and self.request.method in ["GET"]:
            return super().get_authenticators()
        return [CustomAuthentication()]

    def get_queryset(self):
        if self.action in ["create", "update"]:
            # We need to prefetch the price object if it exists to validate the
            # price_id field, and the proof object to validate the proof_id
            # field
            return PriceTag.objects.select_related("proof", "price").all()
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
                "open_prices.proofs.ml.price_tags.update_price_tag_extraction",
                price_tag.id,
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
    ordering_fields = ["id", "proof_id", "order", "status", "created"]
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
