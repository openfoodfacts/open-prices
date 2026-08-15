import django_filters
from django import forms

from open_prices.api.utils import ArrayFieldElementContainsFilter
from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.products import constants as product_constants
from open_prices.proofs import constants as proof_constants

NEARBY_PARAMETER_NAMES = ("lat", "lon", "radius_km")


class PriceFilterForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        provided_parameters = {
            name for name in NEARBY_PARAMETER_NAMES if name in self.data
        }
        has_empty_parameter = any(
            self.data.get(name) in (None, "") for name in provided_parameters
        )
        if provided_parameters and (
            len(provided_parameters) != len(NEARBY_PARAMETER_NAMES)
            or has_empty_parameter
        ):
            raise forms.ValidationError(
                "lat, lon and radius_km must be provided together with non-empty "
                "values."
            )
        return cleaned_data


class PriceFilter(django_filters.FilterSet):
    """
    PriceViewSet GET queryset has select_related on product, location, proof
    """

    lat = django_filters.NumberFilter(
        method="ignore_nearby_parameter",
        min_value=-90,
        max_value=90,
        label="Latitude of the center point (-90 to 90). Must be sent together "
        "with lon and radius_km.",
    )
    lon = django_filters.NumberFilter(
        method="ignore_nearby_parameter",
        min_value=-180,
        max_value=180,
        label="Longitude of the center point (-180 to 180). Must be sent together "
        "with lat and radius_km.",
    )
    radius_km = django_filters.NumberFilter(
        method="ignore_nearby_parameter",
        min_value=0,
        label="Search radius in kilometers (0 or more). Must be sent together "
        "with lat and lon.",
    )
    kind = django_filters.ChoiceFilter(
        choices=constants.KIND_CHOICES,
        method="filter_kind",
    )
    product__source = django_filters.ChoiceFilter(
        field_name="product__source",
        choices=product_constants.SOURCE_CHOICES,
    )
    product__source__isnull = django_filters.BooleanFilter(
        field_name="product__source", lookup_expr="isnull"
    )
    product__categories_tags__contains = ArrayFieldElementContainsFilter(
        field_name="product__categories_tags"
    )
    product__categories_tags__overlap = django_filters.BaseInFilter(
        field_name="product__categories_tags",
        lookup_expr="overlap",
    )
    labels_tags__contains = ArrayFieldElementContainsFilter(field_name="labels_tags")
    origins_tags__contains = ArrayFieldElementContainsFilter(field_name="origins_tags")
    location__type = django_filters.ChoiceFilter(
        field_name="location__type",
        choices=location_constants.TYPE_CHOICES,
    )
    proof__type = django_filters.MultipleChoiceFilter(
        field_name="proof__type",
        choices=proof_constants.TYPE_CHOICES,
    )
    tags__contains = ArrayFieldElementContainsFilter(field_name="tags")
    location__osm_name__contains = ArrayFieldElementContainsFilter(
        field_name="location__osm_name"
    )

    def filter_kind(self, queryset, name, value):
        if value == constants.KIND_COMMUNITY:
            return queryset.has_kind_community()
        elif value == constants.KIND_CONSUMPTION:
            return queryset.has_kind_consumption()
        return queryset

    def ignore_nearby_parameter(self, queryset, name, value):
        """Validate nearby parameters without applying them separately."""
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        nearby_parameters = {
            name: self.form.cleaned_data.get(name) for name in NEARBY_PARAMETER_NAMES
        }
        if not all(value is not None for value in nearby_parameters.values()):
            return queryset

        nearby_location_ids = (
            Location.objects.nearby(
                center_lat=float(nearby_parameters["lat"]),
                center_lon=float(nearby_parameters["lon"]),
                radius_km=float(nearby_parameters["radius_km"]),
            )
            .order_by()
            .values("id")
        )
        return queryset.filter(location_id__in=nearby_location_ids)

    class Meta:
        model = Price
        form = PriceFilterForm
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
            "duplicate_of": ["isnull"],
            "created": ["gte", "lte"],
        }
