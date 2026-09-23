import django_filters
from django import forms

from open_prices.locations.models import Location

OSM_TAG_PARAMETER_NAMES = ("osm_tag_key", "osm_tag_value")


class LocationFilterForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        provided_parameters = {
            name for name in OSM_TAG_PARAMETER_NAMES if name in self.data
        }
        has_empty_parameter = any(
            self.data.get(name) in (None, "") for name in provided_parameters
        )
        if provided_parameters and (
            len(provided_parameters) != len(OSM_TAG_PARAMETER_NAMES)
            or has_empty_parameter
        ):
            raise forms.ValidationError(
                "osm_tag_key and osm_tag_value must be provided together with "
                "non-empty values."
            )
        return cleaned_data


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
        form = LocationFilterForm
        fields = ["type", "osm_type", "osm_tag_key", "osm_tag_value", "price_count"]
