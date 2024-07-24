from rest_framework import mixins, viewsets

from open_prices.api.users.serializers import UserSerializer
from open_prices.users.models import User


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.has_prices().all()
    serializer_class = UserSerializer
