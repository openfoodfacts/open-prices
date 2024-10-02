from django.contrib import admin

from open_prices.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "source",
        "product_name",
        "price_count",
        "location_count",
        "created",
    )
    list_filter = ("source",)
    search_fields = ("code",)
