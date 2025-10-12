import datetime

from django.utils import timezone

from open_prices.common import utils
from open_prices.locations import constants as location_constants
from open_prices.proofs import constants as proof_constants


def validate_proof_date_rules(instance):
    """
    - date format should be YYYY-MM-DD
    - date should not be in the future (we accept 1 day leniency for users in future time zones)  # noqa
    """
    errors = dict()
    if instance.date:
        if type(instance.date) is str:
            utils.add_validation_error(
                errors,
                "date",
                "Parsing error. Expected format: YYYY-MM-DD",
            )
        elif instance.date > timezone.now().date() + datetime.timedelta(days=1):
            utils.add_validation_error(
                errors,
                "date",
                "Should not be in the future",
            )
    return errors


def validate_proof_location_rules(instance):
    """
    - allow passing a location_id
    - location_osm_id should be set if location_osm_type is set
    - location_osm_type should be set if location_osm_id is set
    - some location fields should match the proof fields (on create)
    """
    errors = dict()
    if instance.location_id:
        location = None
        from open_prices.locations.models import Location

        try:
            location = Location.objects.get(id=instance.location_id)
        except Location.DoesNotExist:
            utils.add_validation_error(
                errors,
                "location",
                "Location not found",
            )

        if location:
            if location.type == location_constants.TYPE_ONLINE:
                if instance.location_osm_id:
                    utils.add_validation_error(
                        errors,
                        "location_osm_id",
                        f"Should not be set (location type is {location.type})",
                    )
                if instance.location_osm_type:
                    utils.add_validation_error(
                        errors,
                        "location_osm_type",
                        f"Should not be set (location type is {location.type})",
                    )
            elif location.type == location_constants.TYPE_OSM:
                if not instance.id:  # skip these checks on update
                    for LOCATION_FIELD in instance.DUPLICATE_LOCATION_FIELDS:
                        location_field_value = getattr(
                            instance.location, LOCATION_FIELD.replace("location_", "")
                        )
                        if location_field_value:
                            proof_field_value = getattr(instance, LOCATION_FIELD)
                            if str(location_field_value) != str(proof_field_value):
                                utils.add_validation_error(
                                    errors,
                                    "location",
                                    f"Location {LOCATION_FIELD} ({location_field_value}) does not match the proof {LOCATION_FIELD} ({proof_field_value})",
                                )
    else:
        if instance.location_osm_id:
            if not instance.location_osm_type:
                utils.add_validation_error(
                    errors,
                    "location_osm_type",
                    "Should be set if `location_osm_id` is filled",
                )
        if instance.location_osm_type:
            if not instance.location_osm_id:
                utils.add_validation_error(
                    errors,
                    "location_osm_id",
                    "Should be set if `location_osm_type` is filled",
                )
            elif instance.location_osm_id in [True, "true", "false", "none", "null"]:
                utils.add_validation_error(
                    errors,
                    "location_osm_id",
                    "Should not be a boolean or an invalid string",
                )
    return errors


def validate_proof_type_price_tag_rules(instance):
    errors = dict()
    if not instance.type == proof_constants.TYPE_PRICE_TAG:
        if instance.ready_for_price_tag_validation:
            utils.add_validation_error(
                errors,
                "ready_for_price_tag_validation",
                f"Can only be set if type is {proof_constants.TYPE_PRICE_TAG}",
            )
    return errors


def validate_proof_type_receipt_rules(instance):
    errors = dict()
    if not instance.type == proof_constants.TYPE_RECEIPT:
        if instance.receipt_price_count is not None:
            utils.add_validation_error(
                errors,
                "receipt_price_count",
                f"Can only be set if type is {proof_constants.TYPE_RECEIPT}",
            )
        if instance.receipt_price_total is not None:
            utils.add_validation_error(
                errors,
                "receipt_price_total",
                f"Can only be set if type is {proof_constants.TYPE_RECEIPT}",
            )
        if instance.receipt_online_delivery_costs is not None:
            utils.add_validation_error(
                errors,
                "receipt_online_delivery_costs",
                f"Can only be set if type is {proof_constants.TYPE_RECEIPT}",
            )
    return errors


def validate_proof_type_consumption_rules(instance):
    errors = dict()
    if instance.type not in proof_constants.TYPE_GROUP_CONSUMPTION_LIST:
        if instance.owner_consumption is not None:
            errors = utils.add_validation_error(
                errors,
                "owner_consumption",
                f"Can only be set if type is consumption ({proof_constants.TYPE_GROUP_CONSUMPTION_LIST})",
            )
    return errors


def validate_price_tag_bounding_box_rules(instance):
    errors = dict()
    if instance.bounding_box is not None:
        if len(instance.bounding_box) != 4:
            utils.add_validation_error(
                errors,
                "bounding_box",
                "Should have 4 values.",
            )
        else:
            if not all(isinstance(value, float) for value in instance.bounding_box):
                utils.add_validation_error(
                    errors,
                    "bounding_box",
                    "Values should be floats.",
                )
            elif not all(value >= 0 and value <= 1 for value in instance.bounding_box):
                utils.add_validation_error(
                    errors,
                    "bounding_box",
                    "Values should be between 0 and 1.",
                )
            else:
                y_min, x_min, y_max, x_max = instance.bounding_box
                if y_min >= y_max or x_min >= x_max:
                    utils.add_validation_error(
                        errors,
                        "bounding_box",
                        "Values should be in the format [y_min, x_min, y_max, x_max].",
                    )
    return errors


def validate_price_tag_relationship_rules(instance):
    """
    instance.proof and instance.price are fetched with select_related
    in the view (when the action is "create" or "update").
    We therefore only check the validity of the relationship if the user
    tries to update the price tag.
    """
    errors = dict()
    if instance.proof:
        if instance.proof.type != proof_constants.TYPE_PRICE_TAG:
            utils.add_validation_error(
                errors,
                "proof",
                "Should have type PRICE_TAG.",
            )

    if instance.proof_prediction:
        if instance.proof_prediction.proof_id != instance.proof.id:
            utils.add_validation_error(
                errors,
                "proof_prediction",
                "Should belong to the same proof.",
            )

    if instance.price:
        if instance.proof and instance.price.proof_id != instance.proof.id:
            utils.add_validation_error(
                errors,
                "price",
                "Should belong to the same proof.",
            )
        if instance.status is None:
            instance.status = proof_constants.PriceTagStatus.linked_to_price.value
        elif instance.status != proof_constants.PriceTagStatus.linked_to_price.value:
            utils.add_validation_error(
                errors,
                "status",
                "Should be `linked_to_price` when price_id is set.",
            )
    return errors
