"""
A list of rules, to clean up the data
"""

from django.db.models import Q
from django.db.models.functions import Length

from open_prices.prices import constants as price_constants
from open_prices.products.models import Product


def cleanup_products_with_long_barcodes():
    """
    Remove products (and their prices) with long barcodes
    - long barcode = more than 13 characters
    - only if the price come from the validation workflows
    - only from unknown source (aka not from OxF)
    """
    # init
    price_deleted_count = 0
    product_deleted_count = 0

    # products with long barcodes
    product_queryset = Product.objects.annotate(
        code_length_annotated=Length("code")
    ).filter(code_length_annotated__gt=13, source=None)
    print(f"Found {product_queryset.count()} products with long barcodes")

    # build the price source filter query
    source_query = Q()
    for source in price_constants.PRICE_CREATED_FROM_PRICE_TAG_VALIDATION_SOURCE_LIST:
        source_query |= Q(source__contains=source)

    # loop on each product
    for product in product_queryset:
        product_prices_from_source_queryset = product.prices.filter(source_query)
        if product_prices_from_source_queryset.exists():
            for price in product_prices_from_source_queryset.all():
                price.delete()  # delete 1 by 1 to trigger signals
                price_deleted_count += 1
            product.delete()
            product_deleted_count += 1

    # recap
    print(f"Deleted {price_deleted_count} prices and {product_deleted_count} products")
