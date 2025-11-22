from django.contrib import admin

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
class FlagAdmin(admin.ModelAdmin):
    list_display = (
        "content_type",
        "object_id",
        "reason",
        "status",
        "owner",
        "created",
    )
    list_filter = (ContentTypeListFilter, "reason", "status")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
