import django_filters

from open_prices.common import constants
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import PriceTag, Proof, ReceiptItem


class ProofFilter(django_filters.FilterSet):
    """
    ProofViewSet GET queryset has select_related on location
    """

    type = django_filters.MultipleChoiceFilter(
        field_name="type",
        choices=proof_constants.TYPE_CHOICES,
    )
    kind = django_filters.ChoiceFilter(
        choices=constants.KIND_CHOICES,
        method="filter_kind",
    )
    tags__contains = django_filters.CharFilter(field_name="tags", lookup_expr="any")

    def filter_kind(self, queryset, name, value):
        if value == constants.KIND_COMMUNITY:
            return queryset.has_kind_community()
        elif value == constants.KIND_CONSUMPTION:
            return queryset.has_kind_consumption()
        return queryset

    class Meta:
        model = Proof
        fields = {
            "image_md5_hash": ["exact"],
            "location_osm_id": ["exact"],
            "location_osm_type": ["exact"],
            "location_id": ["exact", "in", "isnull"],
            "date": ["exact", "gt", "gte", "lt", "lte", "year", "month"],
            "currency": ["exact"],
            "ready_for_price_tag_validation": ["exact"],
            "price_count": ["exact", "gte", "lte"],
            "prediction_count": ["exact", "gte", "lte"],
            "owner": ["exact"],
            "created": ["gte", "lte"],
        }


class PriceTagFilter(django_filters.FilterSet):
    status__isnull = django_filters.BooleanFilter(
        field_name="status", lookup_expr="isnull"
    )
    prediction_count__gte = django_filters.NumberFilter(
        field_name="prediction_count", lookup_expr="gte"
    )
    prediction_count__lte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="lte"
    )
    tags__contains = django_filters.CharFilter(field_name="tags", lookup_expr="any")
    created__gte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    created__lte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )

    class Meta:
        model = PriceTag
        fields = [
            "proof_id",
            "proof__owner",
            "proof__ready_for_price_tag_validation",
            "price_id",
            "status",
            "prediction_count",
        ]


class ReceiptItemFilter(django_filters.FilterSet):
    status__isnull = django_filters.BooleanFilter(
        field_name="status", lookup_expr="isnull"
    )
    created__gte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    created__lte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )

    class Meta:
        model = ReceiptItem
        fields = ["proof_id", "proof__owner", "status"]
