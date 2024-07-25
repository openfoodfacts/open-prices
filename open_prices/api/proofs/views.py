from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from open_prices.api.proofs.filters import ProofFilter
from open_prices.api.proofs.serializers import (
    ProofFullSerializer,
    ProofUpdateSerializer,
)
from open_prices.common.authentication import CustomAuthentication
from open_prices.proofs.models import Proof


class ProofViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]  # disable "put"
    # queryset = Proof.objects.all()
    # serializer_class = ProofFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProofFilter
    ordering_fields = ["date", "created"]

    def get_queryset(self):
        return Proof.objects.filter(owner=self.request.user.user_id)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ProofUpdateSerializer
        return ProofFullSerializer
