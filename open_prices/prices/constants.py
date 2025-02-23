TYPE_PRODUCT = "PRODUCT"  # product_code
TYPE_CATEGORY = "CATEGORY"  # OFF category_tag (raw product)
TYPE_LIST = [TYPE_PRODUCT, TYPE_CATEGORY]
TYPE_CHOICES = [(key, key) for key in TYPE_LIST]


DISCOUNT_TYPE_QUANTITY = "QUANTITY"  # example: buy 1 get 1 free
DISCOUNT_TYPE_SALE = "SALE"  # example: 50% off
DISCOUNT_TYPE_SEASONAL = "SEASONAL"  # example: Christmas sale
DISCOUNT_TYPE_LOYALTY_PROGRAM = "LOYALTY_PROGRAM"  # example: 10% off for members
DISCOUNT_TYPE_EXPIRES_SOON = "EXPIRES_SOON"  # example: 30% off expiring soon
DISCOUNT_TYPE_PICK_IT_YOURSELF = "PICK_IT_YOURSELF"  # example: 5% off for pick-up
DISCOUNT_TYPE_SECOND_HAND = "SECOND_HAND"  # example: second hand books or clothes
DISCOUNT_TYPE_OTHER = "OTHER"
DISCOUNT_TYPE_LIST = [
    DISCOUNT_TYPE_QUANTITY,
    DISCOUNT_TYPE_SALE,
    DISCOUNT_TYPE_SEASONAL,
    DISCOUNT_TYPE_LOYALTY_PROGRAM,
    DISCOUNT_TYPE_EXPIRES_SOON,
    DISCOUNT_TYPE_PICK_IT_YOURSELF,
    DISCOUNT_TYPE_SECOND_HAND,
    DISCOUNT_TYPE_OTHER,
]
DISCOUNT_TYPE_CHOICES = [(key, key) for key in DISCOUNT_TYPE_LIST]

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
