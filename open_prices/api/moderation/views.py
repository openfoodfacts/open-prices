from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from open_prices.api.moderation.filters import FlagFilter
from open_prices.api.moderation.serializers import FlagSerializer, FlagUpdateSerializer
from open_prices.common.authentication import CustomAuthentication
from open_prices.common.permission import OnlyModeratorIsAllowed
from open_prices.moderation.models import Flag


@extend_schema_view(
    list=extend_schema(tags=["moderation"]),
    partial_update=extend_schema(tags=["moderation"]),
)
class FlagViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated, OnlyModeratorIsAllowed]
    http_method_names = ["get", "patch"]  # disable "put"
    queryset = Flag.objects.all()
    serializer_class = FlagSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = FlagFilter
    ordering_fields = ["id", "reason", "status", "created", "updated"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return FlagUpdateSerializer
        return self.serializer_class
