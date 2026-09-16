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


def rewrite_creation_history_entry(location, field_values: dict) -> None:
    """
    If `location`'s history is still exactly its original "+" entry (i.e.
    nothing else has touched it since creation), rewrite that entry in place
    with `field_values` instead of leaving it showing the near-empty
    pre-enrichment state.
    """
    history_records = list(location.history.all()[:2])
    if len(history_records) == 1 and history_records[0].history_type == "+":
        historical_creation = history_records[0]
        for key, value in field_values.items():
            setattr(historical_creation, key, value)
        historical_creation.save()
