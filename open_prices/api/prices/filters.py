import django_filters

from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.prices.models import Price
from open_prices.products import constants as product_constants
from open_prices.proofs import constants as proof_constants


class PriceFilter(django_filters.FilterSet):
    """
    PriceViewSet GET queryset has select_related on product, location, proof
    """

    kind = django_filters.ChoiceFilter(
        choices=constants.KIND_CHOICES,
        method="filter_kind",
    )
    product__source = django_filters.ChoiceFilter(
        field_name="product__source",
        choices=product_constants.SOURCE_CHOICES,
    )
    product__categories_tags__contains = django_filters.CharFilter(
        field_name="product__categories_tags",
        lookup_expr="any",
    )
    product__categories_tags__overlap = django_filters.BaseInFilter(
        field_name="product__categories_tags",
        lookup_expr="overlap",
    )
    labels_tags__contains = django_filters.CharFilter(
        field_name="labels_tags",
        lookup_expr="icontains",
    )
    origins_tags__contains = django_filters.CharFilter(
        field_name="origins_tags",
        lookup_expr="icontains",
    )
    location__type = django_filters.ChoiceFilter(
        field_name="location__type",
        choices=location_constants.TYPE_CHOICES,
    )
    proof__type = django_filters.MultipleChoiceFilter(
        field_name="proof__type",
        choices=proof_constants.TYPE_CHOICES,
    )
    tags__contains = django_filters.CharFilter(
        field_name="tags",
        lookup_expr="icontains",
    )
    location__osm_name__contains = django_filters.CharFilter(
        field_name="location__osm_name",
        lookup_expr="icontains",
    )

    def filter_kind(self, queryset, name, value):
        if value == constants.KIND_COMMUNITY:
            return queryset.has_kind_community()
        elif value == constants.KIND_CONSUMPTION:
            return queryset.has_kind_consumption()
        return queryset

    class Meta:
        model = Price
        fields = {
            "type": ["exact"],
            "product_code": ["exact", "in", "isnull"],
            "product_id": ["exact", "in", "isnull"],
            "product_name": ["exact"],
            "category_tag": ["exact"],
            "location_osm_id": ["exact"],
            "location_osm_type": ["exact"],
            "location_id": ["exact", "in", "isnull"],
            "price": ["exact", "gt", "gte", "lt", "lte"],
            "price_is_discounted": ["exact"],
            "discount_type": ["exact"],
            "currency": ["exact"],
            "date": ["exact", "gt", "gte", "lt", "lte", "year", "month"],
            "proof_id": ["exact", "in", "isnull"],
            "owner": ["exact"],
            "created": ["gte", "lte"],
        }
