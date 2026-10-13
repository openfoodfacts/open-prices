from rest_framework import serializers

from open_prices.products.models import Product


class ProductImageLanguageSerializer(serializers.Serializer):
    product_language_code = serializers.RegexField(
        regex=r"^[a-z]{2}$",
        default="en",
        error_messages={
            "invalid": "Use a two-letter lowercase language code, such as nl."
        },
    )


class ProductFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
