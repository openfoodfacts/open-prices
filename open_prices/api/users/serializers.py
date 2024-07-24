from rest_framework import serializers

from open_prices.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.SERIALIZED_FIELDS
