from openfoodfacts import Flavor
from rest_framework import serializers

from open_prices.common.openfoodfacts import normalize_language_code
from open_prices.products.models import Product


class ProductFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ProductOffRequestSerializer(serializers.Serializer):
    """Payload of the OFF actions (off-update & off-upload-image)."""

    flavor = serializers.ChoiceField(
        choices=[flavor.value for flavor in Flavor], default=Flavor.off.value
    )
    product_language_code = serializers.CharField(default="en")

    def validate_product_language_code(self, value):
        language_code = normalize_language_code(value)
        if not language_code:
            raise serializers.ValidationError("Invalid language code")
        return language_code


class ProductOffUpdateRequestSerializer(ProductOffRequestSerializer):
    update_params = serializers.DictField(default=dict)


class ProductOffUploadImageRequestSerializer(ProductOffRequestSerializer):
    image_data_base64 = serializers.CharField()
