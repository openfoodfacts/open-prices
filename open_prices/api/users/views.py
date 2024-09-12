from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from open_prices.api.users.filters import UserFilter
from open_prices.api.users.serializers import UserSerializer
from open_prices.users.models import User


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.has_prices().all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = UserFilter
    ordering_fields = [
        "user_id",
        "price_count",
        "location_count",
        "product_count",
        "proof_count",
    ]
    ordering = ["user_id"]
