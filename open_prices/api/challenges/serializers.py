from rest_framework import serializers

from open_prices.challenges.models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    tag = serializers.CharField(read_only=True)

    class Meta:
        model = Challenge
        fields = "__all__"
