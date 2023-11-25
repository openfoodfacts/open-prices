from enum import Enum

from babel.numbers import list_currencies

CURRENCIES = [(currency, currency) for currency in list_currencies()]

CurrencyEnum = Enum("CurrencyEnum", CURRENCIES)


class LocationOSMType(Enum):
    NODE = "NODE"
    WAY = "WAY"
    RELATION = "RELATION"
