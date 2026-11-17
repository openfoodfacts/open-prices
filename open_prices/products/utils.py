from django.db.models import Avg

from open_prices.products.models import Product


def calculate_price_estimate(product: Product):
    """
    Calculate the price estimate for a product
    - get only non-discounted prices
    - get the price values, and calculate the average
    TODO
    - add a filter to get only the prices from the last X months?
    - remove outliers?
    """
    price_qs = product.prices.with_extra_fields().exclude(
        price_without_discount_annotated__isnull=True
    )
    # price_qs = price_qs.order_by("-date")
    price_values = price_qs.values_list("price_without_discount_annotated", flat=True)
    return price_values.aggregate(Avg("price_without_discount_annotated"))[
        "price_without_discount_annotated__avg"
    ]
