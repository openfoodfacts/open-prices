from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from open_prices.api.users.filters import UserFilter
from open_prices.api.users.serializers import UserSerializer
from open_prices.users.models import User


class UserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = []
    permission_classes = []
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "user_id"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = UserFilter
    ordering_fields = User.SERIALIZED_FIELDS
    ordering = ["user_id"]

    def get_queryset(self):
        # list: return only users with prices
        if not self.kwargs.get("user_id", None):
            return self.queryset.has_prices()
        return self.queryset
