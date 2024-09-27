from django.contrib import admin

from open_prices.locations.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "osm_id",
        "osm_type",
        "osm_name",
        "osm_tag_key",
        "osm_tag_value",
        "price_count",
        "user_count",
        "product_count",
        "proof_count",
        "created",
    )
    list_filter = ("osm_type",)
    search_fields = ("osm_id",)
