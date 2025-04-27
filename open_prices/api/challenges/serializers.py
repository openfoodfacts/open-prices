from rest_framework import serializers

from open_prices.challenges.models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="status", read_only=True)
    tag = serializers.CharField(source="tag", read_only=True)

    class Meta:
        model = Challenge
        fields = "__all__"
