TYPE_PRODUCT = "PRODUCT"  # product_code
TYPE_CATEGORY = "CATEGORY"  # OFF category_tag (raw product)
TYPE_LIST = [TYPE_PRODUCT, TYPE_CATEGORY]
TYPE_CHOICES = [(key, key) for key in TYPE_LIST]


"""
PRICE_PER
For raw products (TYPE_CATEGORY) (fruits, vegetables, etc.),
the price is either per unit or per kilogram.
"""
PRICE_PER_UNIT = "UNIT"
PRICE_PER_KILOGRAM = "KILOGRAM"
PRICE_PER_LIST = [PRICE_PER_UNIT, PRICE_PER_KILOGRAM]
PRICE_PER_CHOICES = [(key, key) for key in PRICE_PER_LIST]


PRICE_CREATED_FROM_PRICE_TAG_VALIDATION_SOURCE_LIST = [
    "/experiments/price-validation-assistant",
    "/experiments/contribution-assistant",
]
