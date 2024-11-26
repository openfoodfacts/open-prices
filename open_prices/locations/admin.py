from django.contrib import admin

from open_prices.locations.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "osm_id",
        "osm_type",
        "osm_name",
        "website_url",
        "price_count",
        "user_count",
        "product_count",
        "proof_count",
        "created",
    )
    list_filter = ("type", "osm_type")
    search_fields = ("osm_id",)
