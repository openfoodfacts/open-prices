from django.contrib import admin

from open_prices.proofs.models import Proof


@admin.register(Proof)
class ProofAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "location",
        "date",
        "currency",
        "price_count",
        "owner",
        "created",
    )
    list_filter = ("type",)
