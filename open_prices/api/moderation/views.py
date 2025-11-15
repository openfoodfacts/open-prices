from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from open_prices.api.moderation.serializers import FlagSerializer
from open_prices.common.authentication import CustomAuthentication
from open_prices.common.permission import OnlyModeratorIsAllowed
from open_prices.moderation.models import Flag


class FlagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Allow moderators to view all flags.
    """

    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated, OnlyModeratorIsAllowed]
    queryset = Flag.objects.all()
    serializer_class = FlagSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["id", "reason", "status", "created", "updated"]
    ordering = ["id"]
