from rest_framework import serializers

from open_prices.api.locations.serializers import LocationFullSerializer
from open_prices.api.products.serializers import ProductFullSerializer
from open_prices.api.proofs.serializers import ProofSerializer
from open_prices.prices.models import Price


class PriceFullSerializer(serializers.ModelSerializer):
    product = ProductFullSerializer()
    location = LocationFullSerializer()
    proof = ProofSerializer()

    class Meta:
        model = Price
        # fields = "__all__"
        exclude = ["source"]


class PriceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = Price.CREATE_FIELDS


class PriceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = Price.UPDATE_FIELDS