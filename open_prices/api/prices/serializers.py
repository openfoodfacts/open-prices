from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.api.products.serializers import ProductFullSerializer
from open_prices.api.proofs.serializers import ProofSerializer
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.products.models import Product
from open_prices.proofs.models import Proof


class PriceSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location"
    )
    proof_id = serializers.PrimaryKeyRelatedField(
        queryset=Proof.objects.all(), source="proof"
    )

    class Meta:
        model = Price
        # fields = "__all__"
        exclude = ["source"]


class PriceFullSerializer(PriceSerializer):
    product = ProductFullSerializer()
    location = LocationSerializer()
    proof = ProofSerializer()

    class Meta:
        model = Price
        exclude = PriceSerializer.Meta.exclude


class PriceCreateSerializer(serializers.ModelSerializer):
    proof_id = serializers.PrimaryKeyRelatedField(
        queryset=Proof.objects.all(), source="proof"
    )

    class Meta:
        model = Price
        fields = Price.CREATE_FIELDS


class PriceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = Price.UPDATE_FIELDS
