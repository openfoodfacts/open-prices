from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from simple_history.admin import SimpleHistoryAdmin

from open_prices.common.admin import ReadOnlyAdminMixin
from open_prices.proofs import constants as proof_constants
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
class PriceTagPredictionAdmin(ReadOnlyAdminMixin, SimpleHistoryAdmin):
    list_display = (
        "id",
        "price_tag",
        "type",
        "model_name",
        "model_version",
        "created",
    )
    list_filter = ("type",)


class PriceTagPredictionInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = PriceTagPrediction
    extra = 0
    fields = ("price_tag", "type", "model_name", "model_version", "created")
    can_delete = False
    show_change_link = True


@admin.register(PriceTag)
class PriceTagAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "prediction_count",
        "tags",
        "created",
    )
    list_filter = ("status",)
    readonly_fields = ("image_display",)  # (all fields are readonly)
    inlines = (PriceTagPredictionInline,)

    @admin.display(description="Image")
    def image_display(self, price_tag):
        if price_tag.image_path_full:
            return mark_safe(
                f'<img src="{price_tag.image_path_full}" title="{price_tag.image_path_full}" />'  # noqa
            )
        else:
            return mark_safe("<div>-</div>")


class PriceTagInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = PriceTag
    extra = 0
    fields = ("status", "prediction_count", "tags", "created")
    can_delete = False
    show_change_link = True


@admin.register(ReceiptItem)
class ReceiptItemAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "created",
    )
    list_filter = ("status",)


class ReceiptItemInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = ReceiptItem
    extra = 0
    fields = ("order", "status", "created")
    can_delete = False
    show_change_link = True


@admin.register(ProofPrediction)
class ProofPredictionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "proof",
        "type",
        "model_name",
        "model_version",
        "created",
    )
    list_filter = ("type",)
    inlines = ()  # see get_inlines

    def get_queryset(self, request):
        return self.model.objects.select_related("proof").prefetch_related(
            "price_tags", "receipt_items"
        )

    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj)
        if obj.type == proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE:
            return inlines + (PriceTagInline,)
        elif obj.type == proof_constants.PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE:
            return inlines + (ReceiptItemInline,)
        else:  # PROOF_PREDICTION_CLASSIFICATION_TYPE
            pass
        return inlines


class ProofPredictionInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = ProofPrediction
    extra = 0
    fields = ("proof", "type", "model_name", "model_version", "created")
    can_delete = False
    show_change_link = True


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
    readonly_fields = (
        "image_md5_hash",
        *Proof.COUNT_FIELDS,
        "tags",
        "created",
        "updated",
        "image_display",
    )
    inlines = (ProofPredictionInline,)  # see get_inlines

    def get_queryset(self, request):
        return self.model.all_objects.select_related("location").prefetch_related(
            "price_tags", "receipt_items"
        )

    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj)
        if obj and obj.type == proof_constants.TYPE_PRICE_TAG:
            return inlines + (PriceTagInline,)
        elif obj and obj.type == proof_constants.TYPE_RECEIPT:
            return inlines + (ReceiptItemInline,)
        else:  # TYPE_GDPR_REQUEST, TYPE_SHOP_IMPORT
            pass
        return inlines

    def location_with_link(self, proof):
        if proof.location:
            url = reverse("admin:locations_location_change", args=[proof.location_id])
            return format_html(f'<a href="{url}">{proof.location}</a>')

    location_with_link.short_description = Proof._meta.get_field(
        "location"
    ).verbose_name

    @admin.display(description="Image thumb (click for full image)")
    def image_display(self, proof):
        if proof.image_thumb_path:
            return mark_safe(
                f'<a href="{proof.file_path_full}" target="_blank">'
                f'<img src="{proof.image_thumb_path_full}" title="{proof.image_thumb_path_full}" />'  # noqa
                f"</a>"
            )
        else:
            return mark_safe("<div>-</div>")
