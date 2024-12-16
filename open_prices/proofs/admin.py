from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from open_prices.proofs.models.proof import Proof


@admin.register(Proof)
class ProofAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "location_with_link",
        "date",
        "currency",
        "price_count",
        "owner",
        "created",
    )
    list_filter = ("type",)

    def location_with_link(self, proof):
        if proof.location:
            url = reverse("admin:locations_location_change", args=[proof.location_id])
            return format_html(f'<a href="{url}">{proof.location}</a>')

    location_with_link.short_description = Proof._meta.get_field(
        "location"
    ).verbose_name
