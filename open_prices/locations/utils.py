from django.utils.text import slugify


def get_brand_logo_url(brand_name: str) -> str:
    """
    Input: Location osm_brand (e.g. "Monoprix")
    Output: URL of the brand logo, using openfoodfacts/brand-images repo

    See https://github.com/openfoodfacts/open-prices/issues/1148
    """
    BRAND_LOGO_URL_PREFIX = "https://raw.githubusercontent.com/openfoodfacts/brand-images/refs/heads/main/xx/stores/"
    BRAND_LOGO_FORMAT = "png"  # svg

    if brand_name:
        brand_slug = slugify(brand_name)
        return f"{BRAND_LOGO_URL_PREFIX}{brand_slug}.{BRAND_LOGO_FORMAT}"
    return ""
