import enum
import json

import google.generativeai as genai
import typing_extensions as typing
from django.conf import settings

genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")


# TODO: what about orther categories ?
class Products(enum.Enum):
    OTHER = "other"
    APPLES = "en:apples"
    APRICOTS = "en:apricots"
    ARTICHOKES = "en:artichokes"
    ASPARAGUS = "en:asparagus"
    AUBERGINES = "en:aubergines"
    AVOCADOS = "en:avocados"
    BANANAS = "en:bananas"
    BEET = "en:beet"
    BERRIES = "en:berries"
    BLACKBERRIES = "en:blackberries"
    BLUEBERRIES = "en:blueberries"
    BOK_CHOY = "en:bok-choy"
    BROCCOLI = "en:broccoli"
    CABBAGES = "en:cabbages"
    CARROTS = "en:carrots"
    CAULIFLOWERS = "en:cauliflowers"
    CELERY = "en:celery"
    CELERY_STALK = "en:celery-stalk"
    CEP_MUSHROOMS = "en:cep-mushrooms"
    CHANTERELLES = "en:chanterelles"
    CHERRIES = "en:cherries"
    CHERRY_TOMATOES = "en:cherry-tomatoes"
    CHICKPEAS = "en:chickpeas"
    CHIVES = "en:chives"
    CLEMENTINES = "en:clementines"
    COCONUTS = "en:coconuts"
    CRANBERRIES = "en:cranberries"
    CUCUMBERS = "en:cucumbers"
    DATES = "en:dates"
    ENDIVES = "en:endives"
    FIGS = "en:figs"
    GARLIC = "en:garlic"
    GINGER = "en:ginger"
    GRAPEFRUITS = "en:grapefruits"
    GRAPES = "en:grapes"
    GREEN_BEANS = "en:green-beans"
    KIWIS = "en:kiwis"
    KAKIS = "en:kakis"
    LEEKS = "en:leeks"
    LEMONS = "en:lemons"
    LETTUCES = "en:lettuces"
    LIMES = "en:limes"
    LYCHEES = "en:lychees"
    MANDARIN_ORANGES = "en:mandarin-oranges"
    MANGOES = "en:mangoes"
    MELONS = "en:melons"
    MUSHROOMS = "en:mushrooms"
    NECTARINES = "en:nectarines"
    ONIONS = "en:onions"
    ORANGES = "en:oranges"
    PAPAYAS = "en:papayas"
    PASSION_FRUITS = "en:passion-fruits"
    PEACHES = "en:peaches"
    PEARS = "en:pears"
    PEAS = "en:peas"
    PEPPERS = "en:peppers"
    PINEAPPLE = "en:pineapple"
    PLUMS = "en:plums"
    POMEGRANATES = "en:pomegranates"
    POMELOS = "en:pomelos"
    POTATOES = "en:potatoes"
    PUMPKINS = "en:pumpkins"
    RADISHES = "en:radishes"
    RASPBERRIES = "en:raspberries"
    RHUBARBS = "en:rhubarbs"
    SCALLIONS = "en:scallions"
    SHALLOTS = "en:shallots"
    SPINACHS = "en:spinachs"
    SPROUTS = "en:sprouts"
    STRAWBERRIES = "en:strawberries"
    TOMATOES = "en:tomatoes"
    TURNIP = "en:turnip"
    WATERMELONS = "en:watermelons"
    WALNUTS = "en:walnuts"
    ZUCCHINI = "en:zucchini"


# TODO: what about other origins ?
class Origin(enum.Enum):
    FRANCE = "en:france"
    ITALY = "en:italy"
    SPAIN = "en:spain"
    POLAND = "en:poland"
    CHINA = "en:china"
    BELGIUM = "en:belgium"
    MOROCCO = "en:morocco"
    PERU = "en:peru"
    PORTUGAL = "en:portugal"
    MEXICO = "en:mexico"
    OTHER = "other"
    UNKNOWN = "unknown"


class Unit(enum.Enum):
    KILOGRAM = "KILOGRAM"
    UNIT = "UNIT"


class Label(typing.TypedDict):
    product: Products
    price: float
    origin: Origin
    unit: Unit
    organic: bool
    barcode: str


class Labels(typing.TypedDict):
    labels: list[Label]


def handle_bulk_labels(images):
    response = model.generate_content(
        [
            "Here are "
            + str(len(images))
            + " pictures containing a label. For each picture of a label, please extract all the following attributes: the product category matching product name, the origin category matching country of origin, the price, is the product organic, the unit (per KILOGRAM or per UNIT) and the barcode. I expect a list of "
            + str(len(images))
            + " labels in your reply, no more, no less. If you cannot decode an attribute, set it to an empty string"
        ]
        + images,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", response_schema=Labels
        ),
    )
    vals = json.loads(response.text)
    return vals
