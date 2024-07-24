import django_filters

from open_prices.prices.models import Price


class PriceFilter(django_filters.FilterSet):
    # product_id__isnull
    price__gt = django_filters.NumberFilter(field_name="price", lookup_expr="gt")
    price__gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price__lt = django_filters.NumberFilter(field_name="price", lookup_expr="lt")
    price__lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    date__gt = django_filters.DateFilter(field_name="date", lookup_expr="gt")
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lt = django_filters.DateFilter(field_name="date", lookup_expr="lt")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    # date__year
    # date__month
    # created__gte
    # created__lte

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
