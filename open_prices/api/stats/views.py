from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from open_prices.api.stats.serializers import TotalStatsSerializer
from open_prices.stats.models import TotalStats


class StatsView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=TotalStatsSerializer, tags=["stats"])
    def get(self, request: Request) -> Response:
        total_stats = TotalStats.get_solo()
        serializer = TotalStatsSerializer(total_stats)
        return Response(serializer.data, status=200)
