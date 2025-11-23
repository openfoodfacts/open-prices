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

from open_prices.api.moderation.serializers import FlagCreateSerializer, FlagSerializer
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
from open_prices.common.permission import OnlyObjectOwnerOrModeratorIsAllowed
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml.price_tags import extract_from_price_tag
from open_prices.proofs.models import PriceTag, Proof, ReceiptItem
from open_prices.proofs.utils import compute_file_md5, store_file


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
        OnlyObjectOwnerOrModeratorIsAllowed,  # for edit & delete
    ]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Proof.objects.all()
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
        if self.request.user.is_authenticated:
            owner = self.request.user.user_id
        else:
            if has_token_from_cookie_or_header(self.request):
                return Response(
                    {
                        "detail": "Authentication failed. Please pass a valid token, or remove it to upload the proof anonymously."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                owner = settings.ANONYMOUS_USER_ID

        # get source
        source = get_source_from_request(self.request)

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

    @extend_schema(request=FlagCreateSerializer, responses=FlagSerializer)
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

        if not settings.TESTING:
            async_task(
                "open_prices.proofs.ml.price_tags.run_and_save_price_tag_extraction_from_id",
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
