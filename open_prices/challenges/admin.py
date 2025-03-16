from django.contrib import admin

from open_prices.challenges.models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "challenge_id",
        "state",
        "title",
        "icon",
        "subtitle",
        "start_date",
        "end_date",
        "categories",
        "example_proof_url",
        "created",
        "updated",
    )
    search_fields = ("challenge_id",)
