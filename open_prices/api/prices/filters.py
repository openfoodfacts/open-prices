import django_filters

from open_prices.common import constants
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants


class PriceFilter(django_filters.FilterSet):
    product_id__isnull = django_filters.BooleanFilter(
        field_name="product_id", lookup_expr="isnull"
    )
    product__categories_tags__contains = django_filters.CharFilter(
        field_name="product__categories_tags", lookup_expr="contains"
    )
    product__categories_tags__overlap = django_filters.BaseInFilter(
        field_name="product__categories_tags",
        lookup_expr="overlap",
        help_text="Provide multiple values as separate query parameters. Example: ?product__categories_tags__overlap=en:breakfasts&product__categories_tags__overlap=en:apples",
    )
    labels_tags__contains = django_filters.CharFilter(
        field_name="labels_tags", lookup_expr="contains"
    )
    origins_tags__contains = django_filters.CharFilter(
        field_name="origins_tags", lookup_expr="contains"
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
    proof__type = django_filters.MultipleChoiceFilter(
        field_name="proof__type",
        choices=proof_constants.TYPE_CHOICES,
    )
    kind = django_filters.ChoiceFilter(
        choices=constants.KIND_CHOICES,
        method="filter_kind",
    )
    date__gt = django_filters.DateFilter(field_name="date", lookup_expr="gt")
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lt = django_filters.DateFilter(field_name="date", lookup_expr="lt")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    date__year = django_filters.NumberFilter(field_name="date", lookup_expr="year")
    date__month = django_filters.NumberFilter(field_name="date", lookup_expr="month")
    tags__contains = django_filters.CharFilter(
        field_name="tags", lookup_expr="contains"
    )
    created__gte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    created__lte = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )
    location__osm_name__contains = django_filters.CharFilter(
        field_name="location__osm_name", lookup_expr="icontains"
    )

    def filter_kind(self, queryset, name, value):
        if value == constants.KIND_COMMUNITY:
            return queryset.has_kind_community()
        elif value == constants.KIND_CONSUMPTION:
            return queryset.has_kind_consumption()
        return queryset

    class Meta:
        model = Price
        fields = [
            "type",
            "product_code",
            "product_id",
            "product_name",
            "category_tag",
            "location_osm_id",
            "location_osm_type",
            "location_id",
            "price",
            "price_is_discounted",
            "discount_type",
            "currency",
            "date",
            "proof_id",
            "owner",
        ]
