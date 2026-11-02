from django import forms
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location


class LocationAdminForm(forms.ModelForm):
    # checkboxes instead of the default comma-separated text input
    tags = forms.MultipleChoiceField(
        choices=location_constants.TAG_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Location
        fields = "__all__"


@admin.register(Location)
class LocationAdmin(SimpleHistoryAdmin):
    form = LocationAdminForm
    list_display = (
        "id",
        "type",
        "osm_id",
        "osm_type",
        "osm_name",
        "osm_address_country",
        "website_url",
        "tags",
        "price_count",
        "user_count",
        "product_count",
        "proof_count",
        "created",
    )
    list_filter = ("type", "osm_type")
    search_fields = ("id", "osm_id", "website_url")
    readonly_fields = (
        *Location.TYPE_OSM_OPTIONAL_FIELDS,
        *Location.COUNT_FIELDS,
        "created",
        "updated",
    )
