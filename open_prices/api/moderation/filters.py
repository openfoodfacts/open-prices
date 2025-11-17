import django_filters

from open_prices.moderation.constants import FLAG_ALLOWED_CONTENT_TYPE_LIST
from open_prices.moderation.models import Flag, FlagReason


class FlagFilter(django_filters.FilterSet):
    content_type = django_filters.MultipleChoiceFilter(
        field_name="content_type__model",
        lookup_expr="iexact",
        choices=[
            (model.upper(), model)
            for app_label, model in FLAG_ALLOWED_CONTENT_TYPE_LIST
        ],
    )
    reason = django_filters.MultipleChoiceFilter(
        field_name="reason",
        choices=FlagReason.choices,
    )

    class Meta:
        model = Flag
        fields = ["object_id", "status"]
