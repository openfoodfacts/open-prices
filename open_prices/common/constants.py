from babel.numbers import list_currencies

KIND_COMMUNITY = "COMMUNITY"
KIND_CONSUMPTION = "CONSUMPTION"
KIND_LIST = [KIND_COMMUNITY, KIND_CONSUMPTION]
KIND_CHOICES = [(key, key) for key in KIND_LIST]

CURRENCY_LIST = sorted(list_currencies())
CURRENCY_CHOICES = [(key, key) for key in CURRENCY_LIST]

SOURCE_WEB = "WEB"  # Open Prices Web App
SOURCE_MOBILE = "MOBILE"  # Smoothie - OpenFoodFacts
SOURCE_API = "API"  # API
SOURCE_OTHER = "OTHER"  # None, MyMeals
SOURCE_LIST = [SOURCE_WEB, SOURCE_MOBILE, SOURCE_API, SOURCE_OTHER]
