import django_filters

from open_prices.products.models import Product


class ProductFilter(django_filters.FilterSet):
    product_name__like = django_filters.CharFilter(
        field_name="product_name", lookup_expr="icontains"
    )
    categories_tags__contains = django_filters.CharFilter(
        field_name="categories_tags", lookup_expr="any"
    )
    labels_tags__contains = django_filters.CharFilter(
        field_name="labels_tags", lookup_expr="any"
    )
    brands_tags__contains = django_filters.CharFilter(
        field_name="brands_tags", lookup_expr="any"
    )
    brands__like = django_filters.CharFilter(
        field_name="brands", lookup_expr="icontains"
    )
    unique_scans_n__gte = django_filters.NumberFilter(
        field_name="unique_scans_n", lookup_expr="gte"
    )
    price_count__gte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="gte"
    )
    price_count__lte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="lte"
    )
    source__isnull = django_filters.BooleanFilter(
        field_name="source", lookup_expr="isnull"
    )

    class Meta:
        model = Product
        fields = [
            "code",
            "source",
            "nutriscore_grade",
            "ecoscore_grade",
            "nova_group",
            "price_count",
        ]
