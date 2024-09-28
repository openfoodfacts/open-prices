from django.contrib import admin
from solo.admin import SingletonModelAdmin

from open_prices.stats.models import TotalStats


@admin.register(TotalStats)
class TotalStatsAdmin(SingletonModelAdmin):
    EXCLUDED_FIELDS = ["id"]

    # to keep order
    def get_fields(self, request, obj=None):
        return [f.name for f in obj._meta.fields if f.name not in self.EXCLUDED_FIELDS]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in obj._meta.fields]
