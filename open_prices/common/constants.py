from babel.numbers import list_currencies

CURRENCY_LIST = sorted(list_currencies())
CURRENCY_CHOICES = [(key, key) for key in CURRENCY_LIST]
