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

# django-q2 task groups
# see Q_CLUSTER settings "save_limit" & "save_limit_per"
TASK_GROUP_FETCH_OPENFOODFACTS = "fetch_openfoodfacts"
TASK_GROUP_FETCH_OPENSTREETMAP = "fetch_openstreetmap"
TASK_GROUP_PRICE_UPDATE_TAGS = "price_update_tags"
TASK_GROUP_PROOF_OCR = "proof_ocr"
TASK_GROUP_PROOF_ML = "proof_ml"
TASK_GROUP_PRICE_TAG_ML = "price_tag_ml"
