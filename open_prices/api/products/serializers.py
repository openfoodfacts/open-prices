from rest_framework import serializers

from open_prices.products.models import Product


class ProductFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
