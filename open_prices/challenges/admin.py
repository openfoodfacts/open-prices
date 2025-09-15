from django.contrib import admin
from django.db.models import Count

from open_prices.challenges.models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_date",
        "end_date",
        "categories",
        "location_count",
        "is_published",
        "status_display",
        "created",
        "updated",
    )
    list_filter = ("is_published",)
    search_fields = ("id",)
    readonly_fields = ("location_count", "stats", "created", "updated")

    def get_queryset(self, request):
        return Challenge.objects.annotate(location_count=Count("locations"))

    @admin.display(description="Locations")
    def location_count(self, obj):
        return obj.location_count  # annotated

    @admin.display(description="Status")
    def status_display(self, obj):
        return obj.status  # property
