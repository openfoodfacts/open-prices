from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from open_prices.api.challenges.filters import ChallengeFilter
from open_prices.api.challenges.serializers import ChallengeSerializer
from open_prices.challenges.models import Challenge


class ChallengeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Challenge.objects.with_status().all()
    serializer_class = ChallengeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ChallengeFilter
    ordering = ["created"]
