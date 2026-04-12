import json

from django.contrib import admin
from django.utils.safestring import mark_safe

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
        "categories_full_count_annotated",
        "location_count_annotated",
        "is_published",
        "status_annotated",
        "created",
        "updated",
    )
    list_filter = ("is_published", StatusFilter)
    search_fields = ("id",)
    readonly_fields = (
        "example_proof_url_display",
        "categories_full",
        "categories_full_count_annotated",
        "location_count_annotated",
        "status_annotated",
        "stats",
        "stats_pretty",
        "created",
        "updated",
    )

    fieldsets = (
        (
            "",
            {
                "fields": (
                    "title",
                    "icon",
                    "subtitle",
                    "example_proof_url",
                    "example_proof_url_display",
                )
            },
        ),
        ("Dates", {"fields": ("start_date", "end_date")}),
        (
            "Categories",
            {
                "fields": (
                    "categories",
                    "categories_full",
                    "categories_full_count_annotated",
                )
            },
        ),
        (
            "Locations",
            {
                "fields": (
                    "locations",
                    "location_count_annotated",
                )
            },
        ),
        ("Status", {"fields": ("is_published", "status_annotated")}),
        ("Stats", {"fields": ("stats_pretty",)}),
        ("Metadata", {"fields": ("created", "updated")}),
    )

    def get_queryset(self, request):
        return Challenge.objects.with_extra_fields()

    @admin.display(description="Image")
    def example_proof_url_display(self, obj):
        if obj.example_proof_url:
            return mark_safe(
                f'<a href="{obj.example_proof_url}" target="_blank">'
                f'<img src="{obj.example_proof_url}" title="{obj.example_proof_url}" height=300 />'  # noqa
                f"</a>"
            )

    @admin.display(description="Categories full")
    def categories_full_count_annotated(self, obj):
        return obj.categories_full_count_annotated

    @admin.display(description="Locations")
    def location_count_annotated(self, obj):
        return obj.location_count_annotated

    @admin.display(description="Status")
    def status_annotated(self, obj):
        return obj.status_annotated

    @admin.display(description="Stats (pretty)")
    def stats_pretty(self, obj):
        data = json.dumps(obj.stats, indent=2)
        return mark_safe(f"<pre>{data}</pre>")
