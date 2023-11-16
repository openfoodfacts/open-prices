import logging

import sentry_sdk
from OSMPythonTools.nominatim import Nominatim
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.schemas import LocationBase


def init_sentry(sentry_dsn: str | None, integrations: list[Integration] | None = None):
    if sentry_dsn:
        integrations = integrations or []
        integrations.append(
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.WARNING,  # Send warning and errors as events
            ),
        )
        sentry_sdk.init(  # type:ignore  # mypy say it's abstract
            sentry_dsn,
            integrations=integrations,
        )


def openstreetmap_nominatim_search(osm_id: int, osm_type: str):
    client = Nominatim()
    search_query = f"{osm_type}/{osm_id}"
    return client.query(search_query, lookup=True).toJSON()


def fetch_location_openstreetmap_details(location: LocationBase):
    location_openstreetmap_details = dict()
    try:
        response = openstreetmap_nominatim_search(
            osm_id=location.osm_id, osm_type=location.osm_type.value.lower()
        )
        if len(response):
            for osm_field in ["name", "display_name", "lat", "lon"]:
                if osm_field in response[0]:
                    location_openstreetmap_details[f"osm_{osm_field}"] = response[0][
                        osm_field
                    ]
            if "address" in response[0]:
                for osm_address_field in ["postcode", "city", "country"]:
                    if osm_address_field in response[0]["address"]:
                        location_openstreetmap_details[
                            f"osm_address_{osm_address_field}"
                        ] = response[0]["address"][osm_address_field]

        return location_openstreetmap_details
    except Exception as e:
        print("fetch_location_openstreetmap_details: error returned from OpenStreetMap")
        print(e)
        return
