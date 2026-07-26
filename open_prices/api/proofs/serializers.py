from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.common import history
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.proofs.models import (
    PriceTag,
    PriceTagPrediction,
    Proof,
    ProofPrediction,
    ReceiptItem,
)


class ProofPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProofPrediction
        fields = [
            "type",
            "model_name",
            "model_version",
            "data",
            "value",
            "max_confidence",
            "created",
        ]


class ProofSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location"
    )

    class Meta:
        model = Proof
        # fields = "__all__"
        exclude = ["location"]


class ProofHalfFullSerializer(ProofSerializer):
    location = LocationSerializer()

    class Meta:
        model = Proof
        fields = "__all__"


class ProofFullSerializer(ProofSerializer):
    location = LocationSerializer()
    predictions = ProofPredictionSerializer(many=True, read_only=True)

    class Meta:
        model = Proof
        fields = "__all__"


class ProofUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, use_url=False)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location", required=False
    )

    class Meta:
        model = Proof
        fields = ["file"] + Proof.CREATE_FIELDS


class ProofDraftUploadSerializer(serializers.ModelSerializer):
    """Serializer for draft proof upload - accepts only the file and type fields."""

    file = serializers.FileField(required=True, use_url=False)

    class Meta:
        model = Proof
        fields = ["file", "type"]


class DraftProofAnonymizeRequestSerializer(serializers.Serializer):
    """Serializer for payload when anonymizing a receipt."""

    bounding_boxes = serializers.ListField(
        child=serializers.ListField(
            child=serializers.FloatField(),
            min_length=4,
            max_length=4,
        ),
        min_length=1,
    )

    def validate_bounding_boxes(self, value):
        for bounding_box in value:
            x_min, y_min, x_max, y_max = bounding_box
            if x_min >= x_max or y_min >= y_max:
                raise serializers.ValidationError(
                    "Bounding box coordinates are invalid"
                )
            if x_min < 0 or y_min < 0 or x_max > 1 or y_max > 1:
                raise serializers.ValidationError(
                    "Bounding box coordinates are out of bounds"
                )
        return value


class ProofCreateSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location", required=False
    )

    class Meta:
        model = Proof
        fields = Proof.FILE_FIELDS + Proof.CREATE_FIELDS


class ProofUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = Proof.UPDATE_FIELDS


class ProofProcessWithGeminiSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(required=True, use_url=False)
    )
    mode = serializers.CharField()  # TODO: this mode param should be used to select the prompt to execute, unimplemented for now


class ProofHistorySerializer(history.HistorySerializer):
    pass


class PriceTagPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceTagPrediction
        fields = [
            "type",
            "model_name",
            "model_version",
            "schema_version",
            "data",
            "created",
        ]


class PriceTagFullSerializer(serializers.ModelSerializer):
    price_id = serializers.PrimaryKeyRelatedField(read_only=True)
    predictions = PriceTagPredictionSerializer(many=True, read_only=True)
    proof = ProofHalfFullSerializer()
    image_path = serializers.CharField(read_only=True)  # from model property

    class Meta:
        model = PriceTag
        exclude = ["price"]


class PriceTagCreateSerializer(serializers.ModelSerializer):
    proof_id = serializers.PrimaryKeyRelatedField(
        queryset=Proof.objects.all(), source="proof"
    )
    price_id = serializers.PrimaryKeyRelatedField(
        queryset=Price.objects.all(), source="price", required=False
    )

    class Meta:
        model = PriceTag
        fields = PriceTag.CREATE_FIELDS


class PriceTagUpdateSerializer(serializers.ModelSerializer):
    price_id = serializers.PrimaryKeyRelatedField(
        queryset=Price.objects.all(), source="price"
    )

    class Meta:
        model = PriceTag
        fields = PriceTag.UPDATE_FIELDS


class ReceiptItemFullSerializer(serializers.ModelSerializer):
    proof_id = serializers.PrimaryKeyRelatedField(
        queryset=Proof.objects.all(), source="proof"
    )
    price_id = serializers.PrimaryKeyRelatedField(
        queryset=Price.objects.all(), source="price"
    )

    class Meta:
        model = ReceiptItem
        exclude = ["price", "proof"]
