from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.locations.models import Location
from open_prices.proofs.models import Proof


class ProofSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location"
    )

    class Meta:
        model = Proof
        # fields = "__all__"
        exclude = ["source"]


class ProofFullSerializer(ProofSerializer):
    location = LocationSerializer()

    class Meta:
        model = Proof
        exclude = ProofSerializer.Meta.exclude


class ProofCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = Proof.FILE_FIELDS + Proof.CREATE_FIELDS


class ProofUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = Proof.UPDATE_FIELDS
