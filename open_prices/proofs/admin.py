from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from open_prices.proofs.models import (
    PriceTag,
    PriceTagPrediction,
    Proof,
    ProofPrediction,
    ReceiptItem,
)


class ProofDraftFilter(admin.SimpleListFilter):
    title = "Include drafts"

    parameter_name = "draft"

    def lookups(self, request, model_admin):
        return (
            (None, "Active only"),
            ("draft", "Drafts only"),
            ("all", "All"),
        )

    # need to override choices otherwise django adds 'all' as the
    # None value choice, whereas in this case None is 'Active'
    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": cl.get_query_string(
                    {
                        self.parameter_name: lookup,
                    },
                    [],
                ),
                "display": title,
            }

    def queryset(self, request, queryset):
        if self.value() == "draft":
            return queryset.filter(draft=True)
        elif self.value() is None:
            return queryset.filter(draft=False)
        return queryset  # "all"


@admin.register(PriceTagPrediction)
class PriceTagPredictionAdmin(SimpleHistoryAdmin):
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
        "draft",
        "created",
    )
    list_filter = ("type", ProofDraftFilter)
    readonly_fields = ("created", "updated")
    inlines = (ProofPredictionInline,)

    def get_queryset(self, request):
        return self.model.all_objects.select_related("location")

    def location_with_link(self, proof):
        if proof.location:
            url = reverse("admin:locations_location_change", args=[proof.location_id])
            return format_html(f'<a href="{url}">{proof.location}</a>')

    location_with_link.short_description = Proof._meta.get_field(
        "location"
    ).verbose_name
