from open_prices.common import utils
from open_prices.locations import constants as location_constants


def validate_location_osm_rules(instance):
    errors = dict()
    if instance.type == location_constants.TYPE_OSM:
        for field_name in instance.TYPE_OSM_MANDATORY_FIELDS:
            if not getattr(instance, field_name):
                errors = utils.add_validation_error(
                    errors, field_name, f"Should be set (type = {instance.type})"
                )
        if instance.osm_id in [True, "true", "false", "none", "null"]:
            errors = utils.add_validation_error(
                errors, "osm_id", "Should not be a boolean or an invalid string"
            )
        for field_name in instance.TYPE_ONLINE_MANDATORY_FIELDS:
            if getattr(instance, field_name):
                errors = utils.add_validation_error(
                    errors, field_name, f"Should not be set (type = {instance.type})"
                )
    return errors


def validate_location_online_rules(instance):
    errors = dict()
    if instance.type == location_constants.TYPE_ONLINE:
        for field_name in instance.TYPE_ONLINE_MANDATORY_FIELDS:
            if not getattr(instance, field_name):
                errors = utils.add_validation_error(
                    errors, field_name, f"Should be set (type = {instance.type})"
                )
        for field_name in instance.TYPE_OSM_MANDATORY_FIELDS:
            if getattr(instance, field_name):
                errors = utils.add_validation_error(
                    errors, field_name, f"Should not be set (type = {instance.type})"
                )
    return errors
