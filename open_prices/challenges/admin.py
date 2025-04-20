from django.contrib import admin

from open_prices.challenges.models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_date",
        "end_date",
        "categories",
        "is_published",
        "status_display",
        "created",
        "updated",
    )
    list_filter = ("is_published",)
    search_fields = ("id",)
    readonly_fields = ("created", "updated")

    @admin.display(description="Status")
    def status_display(self, obj):
        return obj.status
