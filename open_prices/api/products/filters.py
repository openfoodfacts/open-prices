import django_filters

from open_prices.api.utils import ArrayFieldElementContainsFilter
from open_prices.products.models import Product


class ProductFilter(django_filters.FilterSet):
    product_name__like = django_filters.CharFilter(
        field_name="product_name", lookup_expr="icontains"
    )
    categories_tags__contains = ArrayFieldElementContainsFilter(
        field_name="categories_tags"
    )
    labels_tags__contains = ArrayFieldElementContainsFilter(field_name="labels_tags")
    brands_tags__contains = ArrayFieldElementContainsFilter(field_name="brands_tags")
    brands__like = django_filters.CharFilter(
        field_name="brands", lookup_expr="icontains"
    )
    unique_scans_n__gte = django_filters.NumberFilter(
        field_name="unique_scans_n", lookup_expr="gte"
    )
    source__isnull = django_filters.BooleanFilter(
        field_name="source", lookup_expr="isnull"
    )

    class Meta:
        model = Product
        fields = {
            "code": ["exact", "in"],
            "source": ["exact"],
            "nutriscore_grade": ["exact"],
            "ecoscore_grade": ["exact"],
            "nova_group": ["exact"],
            "creator": ["exact"],
            "price_count": ["exact", "gte", "lte"],
        }
