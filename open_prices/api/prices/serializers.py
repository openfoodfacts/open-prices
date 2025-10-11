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
        fields = "__all__"


class PriceFullSerializer(PriceSerializer):
    product = ProductFullSerializer()
    location = LocationSerializer()
    proof = ProofSerializer()  # without location object

    class Meta:
        model = Price
        fields = "__all__"


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


class PriceHistorySerializer(serializers.Serializer):
    history_id = serializers.IntegerField()
    history_date = serializers.DateTimeField()
    history_change_reason = serializers.CharField()
    history_type = serializers.ChoiceField(choices=["+", "~", "-"])
    history_user_id = serializers.CharField()
    changes = serializers.ListField()
