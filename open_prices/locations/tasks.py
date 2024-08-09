from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


def fetch_and_save_data_from_openstreetmap(location: Location):
    location_openstreetmap_details = common_openstreetmap.get_location_dict(location)
    if location_openstreetmap_details:
        for key, value in location_openstreetmap_details.items():
            setattr(location, key, value)
        location.save()
