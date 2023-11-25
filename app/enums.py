from enum import Enum

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
    RETAILER = "RETAILER"
