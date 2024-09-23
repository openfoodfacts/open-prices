import django_filters

from open_prices.prices.models import Price


class PriceFilter(django_filters.FilterSet):
    product_id__isnull = django_filters.BooleanFilter(
        field_name="product_id", lookup_expr="isnull"
    )
    labels_tags__contains = django_filters.CharFilter(
        field_name="labels_tags", lookup_expr="icontains"
    )
    origins_tags__contains = django_filters.CharFilter(
        field_name="origins_tags", lookup_expr="icontains"
    )
    price__gt = django_filters.NumberFilter(field_name="price", lookup_expr="gt")
    price__gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price__lt = django_filters.NumberFilter(field_name="price", lookup_expr="lt")
    price__lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    location_id__isnull = django_filters.BooleanFilter(
        field_name="location_id", lookup_expr="isnull"
    )
    proof_id__isnull = django_filters.BooleanFilter(
        field_name="proof_id", lookup_expr="isnull"
    )
    date__gt = django_filters.DateFilter(field_name="date", lookup_expr="gt")
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lt = django_filters.DateFilter(field_name="date", lookup_expr="lt")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    date__year = django_filters.NumberFilter(field_name="date", lookup_expr="year")
    date__month = django_filters.NumberFilter(field_name="date", lookup_expr="month")
    created__gte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    created__lte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )

    class Meta:
        model = Price
        fields = [
            "product_code",
            "product_id",
            "category_tag",
            "location_osm_id",
            "location_osm_type",
            "location_id",
            "price",
            "price_is_discounted",
            "currency",
            "date",
            "proof_id",
            "owner",
        ]
