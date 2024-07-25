from rest_framework import serializers

from open_prices.api.locations.serializers import LocationFullSerializer
from open_prices.proofs.models import Proof


class ProofFullSerializer(serializers.ModelSerializer):
    location = LocationFullSerializer()

    class Meta:
        model = Proof
        fields = "__all__"


class ProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = "__all__"


class ProofCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = Proof.FILE_FIELDS + Proof.CREATE_FIELDS


class ProofUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = Proof.UPDATE_FIELDS
