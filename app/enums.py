from enum import Enum, unique

from babel.numbers import list_currencies

CURRENCIES = [(currency, currency) for currency in list_currencies()]

CurrencyEnum = Enum("CurrencyEnum", CURRENCIES)


class LocationOSMEnum(Enum):
    NODE = "NODE"
    WAY = "WAY"
    RELATION = "RELATION"


class ProofTypeEnum(Enum):
    PRICE_TAG = "PRICE_TAG"
    RECEIPT = "RECEIPT"
    GDPR_REQUEST = "GDPR_REQUEST"


@unique
class PricePerEnum(Enum):
    """For raw products (fruits, vegetables, etc.), the price is either
    per unit or per kilogram. This enum is used to store this information.
    """

    UNIT = "UNIT"
    KILOGRAM = "KILOGRAM"
