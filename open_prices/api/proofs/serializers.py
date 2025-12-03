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
    mode = (
        serializers.CharField()
    )  # TODO: this mode param should be used to select the prompt to execute, unimplemented for now


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
    image_path = serializers.CharField(
        source="image_path_display", read_only=True
    )  # from model property

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
