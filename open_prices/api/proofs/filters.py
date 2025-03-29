import django_filters

from open_prices.common import constants
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import PriceTag, Proof, ReceiptItem


class ProofFilter(django_filters.FilterSet):
    type = django_filters.MultipleChoiceFilter(
        field_name="type",
        choices=proof_constants.TYPE_CHOICES,
    )
    kind = django_filters.ChoiceFilter(
        choices=constants.KIND_CHOICES,
        method="filter_kind",
    )
    location_id__isnull = django_filters.BooleanFilter(
        field_name="location_id", lookup_expr="isnull"
    )
    date__gt = django_filters.DateFilter(field_name="date", lookup_expr="gt")
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lt = django_filters.DateFilter(field_name="date", lookup_expr="lt")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    date__year = django_filters.NumberFilter(field_name="date", lookup_expr="year")
    date__month = django_filters.NumberFilter(field_name="date", lookup_expr="month")
    price_count__gte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="gte"
    )
    price_count__lte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="lte"
    )
    prediction_count__gte = django_filters.NumberFilter(
        field_name="prediction_count", lookup_expr="gte"
    )
    prediction_count__lte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="lte"
    )
    created__gte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    created__lte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )

    def filter_kind(self, queryset, name, value):
        if value == constants.KIND_COMMUNITY:
            return queryset.has_kind_community()
        elif value == constants.KIND_CONSUMPTION:
            return queryset.has_kind_consumption()
        return queryset

    class Meta:
        model = Proof
        fields = [
            "location_osm_id",
            "location_osm_type",
            "location_id",
            "currency",
            "date",
            "owner",
            "ready_for_price_tag_validation",
            "price_count",
            "prediction_count",
        ]


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
