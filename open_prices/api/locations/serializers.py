from rest_framework import serializers

from open_prices.locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"