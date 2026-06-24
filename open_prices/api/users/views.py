from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.badges.serializers import UserBadgeSerializer
from open_prices.api.users.filters import UserFilter
from open_prices.api.users.serializers import UserSerializer
from open_prices.users.models import User


class UserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "user_id"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = UserFilter
    ordering_fields = ["user_id"] + User.COUNT_FIELDS
    ordering = ["user_id"]

    def get_queryset(self):
        # list: return only users with prices
        if not self.kwargs.get("user_id", None):
            return self.queryset.has_prices()
        return self.queryset

    @extend_schema(responses=UserBadgeSerializer(many=True), filters=False)
    @action(detail=True, methods=["GET"])
    def badges(self, request: Request, user_id=None) -> Response:
        user = self.get_object()
        badges = user.user_badges.select_related("badge").all()
        serializer = UserBadgeSerializer(badges, many=True)
        return Response(serializer.data, status=200)
