import django_filters

from open_prices.moderation import constants as moderation_constants
from open_prices.moderation.models import Flag, FlagReason


class FlagFilter(django_filters.FilterSet):
    # in the serializer we replace the content_type field with model upper
    content_type = django_filters.MultipleChoiceFilter(
        field_name="content_type__model",
        choices=moderation_constants.FLAG_ALLOWED_CONTENT_TYPE_CHOICES_UPPER,
        method="filter_content_type",
    )
    reason = django_filters.MultipleChoiceFilter(
        field_name="reason", choices=FlagReason.choices
    )

    class Meta:
        model = Flag
        fields = ["object_id", "status"]

    def filter_content_type(self, queryset, name, value):
        return queryset.filter_by_content_type_model_list(value)
