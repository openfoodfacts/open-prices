from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from open_prices.api.serializers import StatusSerializer


class StatusView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=StatusSerializer, tags=["status"])
    def get(self, request: Request) -> Response:
        return Response({"status": "running"})
