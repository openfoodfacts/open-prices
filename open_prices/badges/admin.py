from django.contrib import admin
from django.utils.safestring import mark_safe

from open_prices.badges.models import Badge, UserBadge
from open_prices.common.admin import ReadOnlyAdminMixin


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "metric",
        "threshold",
        "user_count",
        "created",
    )
    list_filter = ("metric",)
    readonly_fields = ("image_url_display", *Badge.COUNT_FIELDS, *Badge.META_FIELDS)

    fieldsets = (
        (None, {"fields": ("name", "description", "image_url", "image_url_display")}),
        ("Rules", {"fields": ("metric", "threshold")}),
        ("Stats", {"fields": Badge.COUNT_FIELDS}),
        ("Metadata", {"fields": Badge.META_FIELDS}),
    )

    @admin.display(description="Image")
    def image_url_display(self, obj):
        if obj.image_url:
            return mark_safe(
                f'<a href="{obj.image_url}" target="_blank">'
                f'<img src="{obj.image_url}" title="{obj.image_url}" height=50 />'
                f"</a>"
            )
        return None


@admin.register(UserBadge)
class UserBadgeAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "badge",
        "achieved_at",
    )
    list_filter = ("badge",)
