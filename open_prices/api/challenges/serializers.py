from rest_framework import serializers

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)
    status = serializers.ChoiceField(
        choices=challenge_constants.CHALLENGE_STATUS_CHOICES, read_only=True
    )  # from model property
    tag = serializers.CharField(read_only=True)  # from model property

    class Meta:
        model = Challenge
        fields = "__all__"
