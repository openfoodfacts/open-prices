import django_filters

from open_prices.locations.models import Location


class LocationFilter(django_filters.FilterSet):
    osm_name__like = django_filters.CharFilter(
        field_name="osm_name", lookup_expr="icontains"
    )
    osm_address_city__like = django_filters.CharFilter(
        field_name="osm_address_city", lookup_expr="icontains"
    )
    osm_address_country__like = django_filters.CharFilter(
        field_name="osm_address_country", lookup_expr="icontains"
    )
    price_count__gte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="gte"
    )
    price_count__lte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="lte"
    )

    class Meta:
        model = Location
        fields = ["price_count"]
