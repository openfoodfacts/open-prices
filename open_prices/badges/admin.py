from django.contrib import admin

from open_prices.badges.models import BadgeDefinition


@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "metric",
        "threshold",
        "user_count",
        "created",
    )
    list_filter = ("metric",)
    readonly_fields = (*BadgeDefinition.COUNT_FIELDS, *BadgeDefinition.META_FIELDS)
