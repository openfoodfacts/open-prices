from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from open_prices.proofs.models import (
    PriceTag,
    PriceTagPrediction,
    Proof,
    ProofPrediction,
    ReceiptItem,
)


@admin.register(PriceTagPrediction)
class PriceTagPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "price_tag",
        "type",
        "model_name",
        "model_version",
        "created",
    )
    list_filter = ("type",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PriceTagPredictionInline(admin.TabularInline):
    model = PriceTagPrediction
    extra = 0
    fields = ("price_tag", "type", "model_name", "model_version", "created")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PriceTag)
class PriceTagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "created",
    )
    list_filter = ("status",)
    inlines = (PriceTagPredictionInline,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PriceTagInline(admin.TabularInline):
    model = PriceTag
    extra = 0
    fields = ("status", "created")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReceiptItem)
class ReceiptItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "created",
    )
    list_filter = ("status",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReceiptItemInline(admin.TabularInline):
    model = ReceiptItem
    extra = 0
    fields = ("status", "created")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProofPrediction)
class ProofPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "proof",
        "type",
        "model_name",
        "model_version",
        "created",
    )
    list_filter = ("type",)
    inlines = (PriceTagInline, ReceiptItemInline)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProofPredictionInline(admin.TabularInline):
    model = ProofPrediction
    extra = 0
    fields = ("proof", "type", "model_name", "model_version", "created")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
    readonly_fields = ("created", "updated")
    inlines = (ProofPredictionInline,)

    def location_with_link(self, proof):
        if proof.location:
            url = reverse("admin:locations_location_change", args=[proof.location_id])
            return format_html(f'<a href="{url}">{proof.location}</a>')

    location_with_link.short_description = Proof._meta.get_field(
        "location"
    ).verbose_name
