from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.api.products.serializers import ProductSerializer
from open_prices.prices.models import Price


class PriceFullSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    # proof = ProofSerializer(read_only=True)

    class Meta:
        model = Price
        fields = "__all__"
