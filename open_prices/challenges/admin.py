from django.contrib import admin

from open_prices.challenges.models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_date",
        "end_date",
        "categories",
        "created",
        "updated",
    )
    search_fields = ("id",)
