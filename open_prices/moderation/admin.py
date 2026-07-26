from django.contrib import admin

from open_prices.common.admin import ReadOnlyAdminMixin
from open_prices.moderation import constants as moderation_constants
from open_prices.moderation.models import Flag


class ContentTypeListFilter(admin.SimpleListFilter):
    title = Flag._meta.get_field("content_type").verbose_name
    parameter_name = "content_type"

    def lookups(self, request, model_admin):
        return moderation_constants.FLAG_ALLOWED_CONTENT_TYPE_CHOICES_UPPER

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter_by_content_type_model(self.value())
        return queryset


@admin.register(Flag)
class FlagAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "content_type",
        "object_id",
        "reason",
        "status",
        "owner",
        "created",
    )
    list_filter = (ContentTypeListFilter, "reason", "status")
