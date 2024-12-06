from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.locations.models import Location
from open_prices.proofs.models import Proof, ProofPrediction


class ProofPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProofPrediction
        fields = [
            "type",
            "model_name",
            "model_version",
            "created",
            "data",
            "value",
            "max_confidence",
        ]


class ProofSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location"
    )

    class Meta:
        model = Proof
        # fields = "__all__"
        exclude = ["location", "source"]


class ProofHalfFullSerializer(ProofSerializer):
    location = LocationSerializer()

    class Meta:
        model = Proof
        exclude = ["source"]  # ProofSerializer.Meta.exclude


class ProofFullSerializer(ProofSerializer):
    location = LocationSerializer()
    predictions = ProofPredictionSerializer(many=True, read_only=True)

    class Meta:
        model = Proof
        exclude = ["source"]  # ProofSerializer.Meta.exclude


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
