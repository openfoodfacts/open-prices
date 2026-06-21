from django.contrib import admin

from open_prices.badges.models import Badge


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
    readonly_fields = (*Badge.COUNT_FIELDS, *Badge.META_FIELDS)
