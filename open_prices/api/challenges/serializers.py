from rest_framework import serializers

from open_prices.challenges.models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="status_annotated", read_only=True)

    class Meta:
        model = Challenge
        fields = "__all__"
