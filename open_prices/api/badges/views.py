from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from open_prices.api.badges.serializers import BadgeSerializer
from open_prices.badges.models import Badge


class BadgeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["id", "user_count", "created"]
    ordering = ["id"]
