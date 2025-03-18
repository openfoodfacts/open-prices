"""
A list of rules, to clean up the data
"""
import openfoodfacts
from django.db.models import Q
from django.db.models.functions import Length

from open_prices.prices import constants as price_constants
from open_prices.products.models import Product
from open_prices.proofs.models import ProofPrediction


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
        if not openfoodfacts.barcode.has_valid_check_digit(code)
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


def cleanup_useless_proof_predictions():
    """
    - OBJECT_DETECTION "price_tag_detection" only run on PRICE_TAG proofs
    - RECEIPT_EXTRACTION "gemini" only run on RECEIPT proofs
    """
    proof_prediction_object_detection_qs = ProofPrediction.objects.filter(
        type=price_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE
    ).exclude(proof__type=price_constants.TYPE_PRICE_TAG)
    for proof_prediction in proof_prediction_object_detection_qs:
        proof_prediction.delete()

    proof_prediction_receipt_extraction_qs = ProofPrediction.objects.filter(
        type=price_constants.PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE
    ).exclude(proof__type=price_constants.TYPE_RECEIPT)
    for proof_prediction in proof_prediction_receipt_extraction_qs:
        proof_prediction.delete()
