import django_filters

from open_prices.challenges.models import Challenge


class ChallengeFilter(django_filters.FilterSet):
    start_date__gt = django_filters.DateFilter(
        field_name="start_date", lookup_expr="gt"
    )
    start_date__gte = django_filters.DateFilter(
        field_name="start_date", lookup_expr="gte"
    )
    start_date__lt = django_filters.DateFilter(
        field_name="start_date", lookup_expr="lt"
    )
    start_date__lte = django_filters.DateFilter(
        field_name="start_date", lookup_expr="lte"
    )
    start_date__year = django_filters.NumberFilter(
        field_name="start_date", lookup_expr="year"
    )
    start_date__month = django_filters.NumberFilter(
        field_name="start_date", lookup_expr="month"
    )
    end_date__gt = django_filters.DateFilter(field_name="end_date", lookup_expr="gt")
    end_date__gte = django_filters.DateFilter(field_name="end_date", lookup_expr="gte")
    end_date__lt = django_filters.DateFilter(field_name="end_date", lookup_expr="lt")
    end_date__lte = django_filters.DateFilter(field_name="end_date", lookup_expr="lte")
    end_date__year = django_filters.NumberFilter(
        field_name="end_date", lookup_expr="year"
    )
    end_date__month = django_filters.NumberFilter(
        field_name="end_date", lookup_expr="month"
    )

    class Meta:
        model = Challenge
        fields = ["id", "is_published"]
