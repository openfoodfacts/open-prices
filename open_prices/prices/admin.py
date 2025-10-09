from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from open_prices.prices.models import Price


@admin.register(Price)
class PriceAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "type",
        "product_code",
        "product_with_link",
        "category_tag",
        "price",
        "currency",
        "date",
        "location_with_link",
        "proof_with_link",
        "owner",
        "created",
    )
    list_filter = ("type",)

    def product_with_link(self, price):
        if price.product:
            url = reverse("admin:products_product_change", args=[price.product_id])
            return format_html(f'<a href="{url}">{price.product}</a>')

    product_with_link.short_description = Price._meta.get_field("product").verbose_name

    def location_with_link(self, price):
        if price.location:
            url = reverse("admin:locations_location_change", args=[price.location_id])
            return format_html(f'<a href="{url}">{price.location}</a>')

    location_with_link.short_description = Price._meta.get_field(
        "location"
    ).verbose_name

    def proof_with_link(self, price):
        if price.proof:
            url = reverse("admin:proofs_proof_change", args=[price.id])
            return format_html(f'<a href="{url}">{price}</a>')

    proof_with_link.short_description = Price._meta.get_field("proof").verbose_name
