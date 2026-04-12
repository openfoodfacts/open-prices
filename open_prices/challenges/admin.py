from django.contrib import admin
from django.db.models import Count, F, Func, IntegerField

from open_prices.challenges.models import Challenge


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
    list_filter = ("is_published",)
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
        return Challenge.objects.annotate(
            categories_full_count=Func(
                F("categories_full"),
                1,
                function="array_length",
                output_field=IntegerField(),
            ),
            location_count=Count("locations"),
        )

    @admin.display(description="Categories full")
    def categories_full_count(self, obj):
        return obj.categories_full_count  # annotated

    @admin.display(description="Locations")
    def location_count(self, obj):
        return obj.location_count  # annotated

    @admin.display(description="Status")
    def status_display(self, obj):
        return obj.status  # property
