from babel.numbers import list_currencies

CURRENCY_LIST = [currency.upper() for currency in list_currencies()]
CURRENCY_CHOICES = [(key, key) for key in CURRENCY_LIST]
