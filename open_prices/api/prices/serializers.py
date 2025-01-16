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
    proof = ProofSerializer()  # without location object

    class Meta:
        model = Price
        exclude = PriceSerializer.Meta.exclude


class PriceCreateSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location", required=False
    )
    proof_id = serializers.PrimaryKeyRelatedField(
        queryset=Proof.objects.all(), source="proof"
    )

    class Meta:
        model = Price
        fields = Price.CREATE_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].required = False


class PriceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = Price.UPDATE_FIELDS


class PriceStatsSerializer(serializers.Serializer):
    price__count = serializers.IntegerField()
    price__min = serializers.DecimalField(max_digits=10, decimal_places=2)
    price__max = serializers.DecimalField(max_digits=10, decimal_places=2)
    price__avg = serializers.DecimalField(max_digits=10, decimal_places=2)
    price__sum = serializers.DecimalField(max_digits=10, decimal_places=2)


class GroupedPriceStatsQuerySerializer(serializers.Serializer):
    group_by = serializers.CharField(
        required=True, help_text="Field by which to group the statistics"
    )
    order_by = serializers.CharField(
        required=False, help_text="Field by which to order the results"
    )


class GroupedPriceStatsSerializer(PriceStatsSerializer):
    # Override representation to dynamically include the group field
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Add the grouping field dynamically
        for key in instance:
            if key not in representation:  # It's likely the group field
                representation[key] = instance[key]

        return representation
