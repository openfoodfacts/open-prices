from django.contrib import admin

from open_prices.moderation.models import Flag


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
    list_filter = ("status",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
