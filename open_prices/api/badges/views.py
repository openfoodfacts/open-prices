from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.badges.serializers import BadgeSerializer, BadgeUserSerializer
from open_prices.badges.models import Badge


class BadgeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["id", "user_count", "created"]
    ordering = ["id"]

    @extend_schema(responses=BadgeUserSerializer(many=True), filters=False)
    @action(detail=True, methods=["GET"])
    def users(self, request: Request, pk=None) -> Response:
        badge = self.get_object()
        users = badge.user_badges.select_related("user").all()
        serializer = BadgeUserSerializer(users, many=True)
        return Response(serializer.data, status=200)
