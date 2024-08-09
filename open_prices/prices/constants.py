"""For raw products (fruits, vegetables, etc.), the price is either
per unit or per kilogram. This enum is used to store this information.
"""

PRICE_PER_UNIT = "UNIT"
PRICE_PER_KILOGRAM = "KILOGRAM"

PRICE_PER_LIST = [PRICE_PER_UNIT, PRICE_PER_KILOGRAM]
PRICE_PER_CHOICES = [(key, key) for key in PRICE_PER_LIST]
