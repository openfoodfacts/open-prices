from open_prices.locations.models import Location

MAPPING = {
    "7-Eleven": "7-eleven.svg",
    "Aldi": "Aldi.svg",  # match
    "Auchan": "Auchan.svg",  # match
    "Auchan Supermarché": "Auchan.svg",
    "Billa": "Billa.svg",  # match
    "Bio C' Bon": "BiocBon2.jpg",
    "Biocoop": "France/Biocoop.svg",
    "Carrefour": "Carrefour.svg",  # match
    "Carrefour City": "Carrefour.svg",
    "Carrefour Market": "Carrefour.svg",
    "Casino": "France/Casino-Supermarchés.svg",
    "Colruyt": "Colruyt.svg",  # match
    "Delhaize": "Ahold-Delhaize.svg",
    "E.Leclerc": "E.Leclerc.svg",  # match
    "E. Leclerc": "E.Leclerc.svg",
    "E. Leclerc Drive": "E.Leclerc.svg",
    "Centre Commercial E.Leclerc": "E.Leclerc.svg",
    "Edeka": "Edeka.svg",  # match
    "EDEKA": "Edeka.svg",
    "Extra": "Extra.svg",  # match
    "Franprix": "Franprix.svg",  # match
    "Grocery Outlet": "Grocery-Outlet.svg",  # match
    "Intermarché": "Intermarché.svg",  # match
    "Intermarché Super": "Intermarché.svg",
    "Intermarché Contact": "Intermarché.svg",
    "Kiwi": "KIWI.jpg",
    "Lidl": "Lidl.svg",  # match
    "Migros": "Migros.svg",  # match
    "Monoprix": "Monoprix.png",
    "Naturalia": "France/Naturalia.png",
    "Netto": "Netto.svg",  # match
    "Netto City": "Netto.svg",
    "Netto Marken-Discount": "Netto-Marken-Discount-2018.svg",
    "Plodine": "Plodine.svg",  # match
    "Rema 1000": "Rema-1000.jpg",
    "REWE": "REWE.svg",  # match
    "Rossmann": "Rossmann.svg",  # match
    "Sale": "Sale-wordmark.svg",
    "Safeway": "Safeway.svg",  # match
    "Spar": "Spar.svg",  # match
    "Trader Joe's": "Trader-Joes.svg",
    "U Express": "France/U_Express_logo_2009.svg.png",
    "Utile": "France/Utile_logo_2009.svg.png",
    "Hyper U": "France/Hyper_U_logo_2009.png",
    "Super U": "France/Super_U_logo.png",
    "Walmart": "Walmart.svg",  # match
    "Willys": "Willys.svg",  # match
    "Whole Foods Market": "United States/Whole-Foods-Market.svg",
}
# missing: Delhaize, L'eau Vive, Botanic, Circle K


def map_location_name_to_logo_filename(location_name: str) -> str:
    if location_name in MAPPING:
        return MAPPING[location_name]


def get_location_logo_image_path_full(location: Location) -> str:
    """
    We fetch logos from https://github.com/openfoodfacts/brand-images
    """
    image_path_prefix = "https://raw.githubusercontent.com/openfoodfacts/brand-images/refs/heads/main/xx/stores/"

    location_logo_filename = ""
    if location.osm_brand:
        location_logo_filename = map_location_name_to_logo_filename(location.osm_brand)
    elif location.osm_name:
        location_logo_filename = map_location_name_to_logo_filename(location.osm_name)
    elif location.website_url:
        location_logo_filename = map_location_name_to_logo_filename(
            location.website_url
        )

    if location_logo_filename:
        return f"{image_path_prefix}{location_logo_filename}"

    return ""
