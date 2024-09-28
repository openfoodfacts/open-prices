from rest_framework import serializers

from open_prices.stats.models import TotalStats


class TotalStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TotalStats
        # fields = "__all__"
        exclude = ["id", "created"]
