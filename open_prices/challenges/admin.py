from django.contrib import admin

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.models import Challenge


class StatusFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return challenge_constants.CHALLENGE_STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status_annotated=self.value())
        return queryset


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_date",
        "end_date",
        "categories",
        "categories_full_count",
        "location_count",
        "is_published",
        "status_display",
        "created",
        "updated",
    )
    list_filter = ("is_published", StatusFilter)
    search_fields = ("id",)
    readonly_fields = (
        "categories_full",
        "categories_full_count",
        "location_count",
        "stats",
        "created",
        "updated",
    )

    def get_queryset(self, request):
        return Challenge.objects.with_extra_fields()

    @admin.display(description="Categories full")
    def categories_full_count(self, obj):
        return obj.categories_full_count_annotated

    @admin.display(description="Locations")
    def location_count(self, obj):
        return obj.location_count_annotated

    @admin.display(description="Status")
    def status_display(self, obj):
        return obj.status_annotated
