from enum import StrEnum, unique

from babel.numbers import list_currencies

CURRENCIES: tuple[tuple[str, str], ...] = tuple(
    (currency.upper(), currency.upper()) for currency in list_currencies()
)

# Not supported by mypy, see https://github.com/python/mypy/issues/5317
CurrencyEnum = StrEnum("CurrencyEnum", CURRENCIES)  # type: ignore


class LocationOSMEnum(StrEnum):
    NODE = "NODE"
    WAY = "WAY"
    RELATION = "RELATION"


class ProofTypeEnum(StrEnum):
    PRICE_TAG = "PRICE_TAG"
    RECEIPT = "RECEIPT"
    GDPR_REQUEST = "GDPR_REQUEST"


@unique
class PricePerEnum(StrEnum):
    """For raw products (fruits, vegetables, etc.), the price is either
    per unit or per kilogram. This enum is used to store this information.
    """

    UNIT = "UNIT"
    KILOGRAM = "KILOGRAM"
