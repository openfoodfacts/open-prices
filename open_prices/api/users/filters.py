import django_filters

from open_prices.users.models import User


class UserFilter(django_filters.FilterSet):
    price_count__gte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="gte"
    )
    price_count__lte = django_filters.NumberFilter(
        field_name="price_count", lookup_expr="lte"
    )

    class Meta:
        model = User
        fields = ["price_count"]
