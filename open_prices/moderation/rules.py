"""
A list of rules, to clean up the data
"""

import logging
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.functions import Length
from django.utils import timezone

from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.moderation.models import Flag, FlagReason
from open_prices.prices import constants as price_constants
from open_prices.prices.outlier_detection import find_outliers
from open_prices.products.models import Product

logger = logging.getLogger(__name__)


def cleanup_products_with_long_barcodes():
    """
    Remove products (and their prices) that have (too) long barcodes
    - long barcode = more than 13 characters
    - only if the product has an unknown source (aka not from OxF)
    - only if the price came from the validation workflows
    """
    # init
    product_deleted_count = 0
    price_deleted_count = 0

    # products with long barcodes
    product_queryset = Product.objects.annotate(
        code_length_annotated=Length("code")
    ).filter(source=None, code_length_annotated__gt=13)
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
            if product.prices.count() == 0:
                product.delete()
                product_deleted_count += 1

    # recap
    print(f"Deleted {product_deleted_count} products and {price_deleted_count} prices")


def cleanup_products_with_invalid_barcodes():
    """
    Remove products (and their prices) that have invalid barcodes
    invalid barcode = invalid check digit
    - only if the product has an unknown source (aka not from OxF)
    - only if the price came from the validation workflows
    """
    # init
    product_deleted_count = 0
    price_deleted_count = 0

    # products with invalid barcodes
    product_code_list = Product.objects.filter(source=None).values_list(
        "code", flat=True
    )
    product_code_invalid_list = [
        code
        for code in product_code_list
        if not common_openfoodfacts.barcode_is_valid(code)
    ]
    product_queryset = Product.objects.filter(code__in=product_code_invalid_list)
    print(f"Found {product_queryset.count()} products with invalid barcodes")

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
            if product.prices.count() == 0:
                product.delete()
                product_deleted_count += 1

    # recap
    print(f"Deleted {product_deleted_count} products and {price_deleted_count} prices")


def create_flags_from_price_outliers():
    """Create flags for each outlier detected, for prices that were created the day before.

    By running this task after midnight (UTC), and refreshing the `price_statistics_5y` after,
    we ensure that new prices don't skew the median value, that is used to detect outliers.
    """
    yesterday = (timezone.now() - timedelta(days=1)).date()
    outliers = list(find_outliers(target_date=yesterday))

    # As we cannot directly filter per content type without adding a GenericRelation
    # to the Price model, we simply fetch the content type associated with the price
    # table here
    price_content_type = ContentType.objects.get(app_label="prices", model="price")
    for price in outliers:
        is_higher = price.price >= price.median
        if Flag.objects.filter(
            object_id=price.id,
            content_type=price_content_type,
            reason=FlagReason.WRONG_PRICE_VALUE,
        ).count():
            continue
        flag = Flag.objects.create(
            content_object=price,
            reason=FlagReason.WRONG_PRICE_VALUE,
            source="outlier-detection",
            comment=(
                f"Price is {'higher' if is_higher else 'lower'} than "
                f"{'3 * median' if is_higher else 'median / 3'} "
                f"(price: {price.price}, median: {price.median})"
            ),
        )
        logger.info("New flag created for price outlier %s: %s", price.id, flag)
