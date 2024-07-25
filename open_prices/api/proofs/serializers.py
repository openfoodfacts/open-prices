from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.proofs.models import Proof


class ProofFullSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Proof
        fields = "__all__"


class ProofUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = ["type", "currency", "date"]
