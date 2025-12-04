from open_prices.locations.models import Location


def get_location_logo_image_path_full(location: Location) -> str:
    """
    We fetch logos from https://github.com/openfoodfacts/brand-images
    """
    image_path_prefix = "https://raw.githubusercontent.com/openfoodfacts/brand-images/refs/heads/main/xx/stores/"
    return f"{image_path_prefix}{location.name}"
