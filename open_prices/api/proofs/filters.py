import django_filters

from open_prices.proofs.models import Proof


class ProofFilter(django_filters.FilterSet):
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
    created__gte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    created__lte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )

    class Meta:
        model = Proof
        fields = [
            "type",
            "location_osm_id",
            "location_osm_type",
            "location_id",
            "currency",
            "date",
            "owner",
            "price_count",
        ]
