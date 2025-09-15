from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.challenges.models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)  # property
    tag = serializers.CharField(read_only=True)  # property

    class Meta:
        model = Challenge
        fields = "__all__"
