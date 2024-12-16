import enum

from babel.numbers import list_currencies

CURRENCY_LIST = sorted(list_currencies())
CURRENCY_CHOICES = [(key, key) for key in CURRENCY_LIST]


class PriceTagStatus(enum.IntEnum):
    deleted = 0
    linked_to_price = 1
    not_readable = 2
    not_price_tag = 3


PRICE_TAG_STATUS_CHOICES = [(item.value, item.name) for item in PriceTagStatus]
