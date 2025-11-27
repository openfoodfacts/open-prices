from django.utils import timezone

from open_prices.common import openfoodfacts, utils
from open_prices.locations import constants as location_constants
from open_prices.prices import constants as price_constants
from open_prices.proofs import constants as proof_constants


def validate_price_product_code_or_category_tag_rules(instance):
    """
    - if product_code is set, then should be a valid string
    - if product_code is set, then category_tag/labels_tags/origins_tags should not be set  # noqa
    - if category_tag is set, it should be language-prefixed
    - if labels_tags is set, then all labels_tags should be valid taxonomy strings  # noqa
    - if origins_tags is set, then all origins_tags should be valid taxonomy strings  # noqa
    """
    errors = dict()
    if instance.product_code:
        if instance.type != price_constants.TYPE_PRODUCT:
            utils.add_validation_error(
                errors,
                "type",
                f"Should be set to {price_constants.TYPE_PRODUCT} if `product_code` is filled",
            )
        if not isinstance(instance.product_code, str):
            utils.add_validation_error(errors, "product_code", "Should be a string")
        if not instance.product_code.isalnum():
            utils.add_validation_error(
                errors,
                "product_code",
                "Should only contain numbers (or letters)",
            )
        if instance.product_code.lower() in ["true", "false", "none", "null"]:
            utils.add_validation_error(
                errors,
                "product_code",
                "Should not be a boolean or an invalid string",
            )
        for field_name in instance.TYPE_CATEGORY_FIELDS:
            if getattr(instance, field_name):
                utils.add_validation_error(
                    errors,
                    field_name,
                    "Should not be set if `product_code` is filled",
                )
            # cleanup: unset
            setattr(instance, field_name, None)
    elif instance.category_tag:
        if instance.type != price_constants.TYPE_CATEGORY:
            utils.add_validation_error(
                errors,
                "type",
                "Should be set to 'CATEGORY' if `category_tag` is filled",
            )
        try:
            # cleanup: normalize
            instance.category_tag = openfoodfacts.normalize_taxonomized_tags(
                "category", [instance.category_tag]
            )[0]
        except ValueError as e:
            # The value is not language-prefixed
            utils.add_validation_error(
                errors,
                "category_tag",
                str(e),
            )
        if instance.labels_tags:
            if not isinstance(instance.labels_tags, list):
                utils.add_validation_error(
                    errors,
                    "labels_tags",
                    "Should be a list",
                )
            else:
                try:
                    instance.labels_tags = openfoodfacts.normalize_taxonomized_tags(
                        "label", instance.labels_tags
                    )
                except ValueError as e:
                    utils.add_validation_error(
                        errors,
                        "labels_tags",
                        str(e),
                    )
        else:
            # cleanup: normalize
            instance.labels_tags = []
        if instance.origins_tags:
            if not isinstance(instance.origins_tags, list):
                utils.add_validation_error(
                    errors,
                    "origins_tags",
                    "Should be a list",
                )
            else:
                try:
                    instance.origins_tags = openfoodfacts.normalize_taxonomized_tags(
                        "origin", instance.origins_tags
                    )
                except ValueError as e:
                    utils.add_validation_error(
                        errors,
                        "origins_tags",
                        str(e),
                    )
        else:
            # cleanup: normalize
            instance.origins_tags = []  # "en:unknown" ?
    else:
        utils.add_validation_error(
            errors,
            "product_code",
            "Should be set if `category_tag` is not filled",
        )
    return errors


def validate_price_price_rules(instance):
    """
    - price must be set
    - price_is_discounted must be set if price_without_discount is set
    - price_without_discount must be greater or equal to price
    - price_per should be set if category_tag is set
    - discount_type can only be set if price_is_discounted is True
    """
    errors = dict()
    if instance.price in [None, "true", "false", "none", "null"]:
        utils.add_validation_error(
            errors,
            "price",
            "Should not be a boolean or an invalid string",
        )
    else:
        if instance.price_without_discount:
            if not instance.price_is_discounted:
                utils.add_validation_error(
                    errors,
                    "price_is_discounted",
                    "Should be set to True if `price_without_discount` is filled",
                )
            if (
                utils.is_float(instance.price)
                and utils.is_float(instance.price_without_discount)
                and (instance.price_without_discount <= instance.price)
            ):
                utils.add_validation_error(
                    errors,
                    "price_without_discount",
                    "Should be greater than `price`",
                )
        if instance.discount_type:
            if not instance.price_is_discounted:
                utils.add_validation_error(
                    errors,
                    "discount_type",
                    "Should not be set if `price_is_discounted` is False",
                )
    if instance.product_code:
        if instance.price_per:
            utils.add_validation_error(
                errors,
                "price_per",
                "Should not be set if `product_code` is filled",
            )
    if instance.category_tag:
        if not instance.price_per:
            utils.add_validation_error(
                errors,
                "price_per",
                "Should be set if `category_tag` is filled",
            )
    return errors


def validate_price_date_rules(instance):
    """
    - date should have the right format
    - date should not be in the future
    """
    errors = dict()
    if instance.date:
        if type(instance.date) is str:
            utils.add_validation_error(
                errors,
                "date",
                "Parsing error. Expected format: YYYY-MM-DD",
            )
        elif instance.date > timezone.now().date():
            utils.add_validation_error(
                errors,
                "date",
                "Should not be in the future",
            )
    return errors


def validate_price_location_rules(instance):
    """
    - allow passing a location_id
    - location_osm_id should be set if location_osm_type is set
    - location_osm_type should be set if location_osm_id is set
    - some location fields should match the price fields (on create)
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
                        "Can only be set if location type is OSM",
                    )
                if instance.location_osm_type:
                    utils.add_validation_error(
                        errors,
                        "location_osm_type",
                        "Can only be set if location type is OSM",
                    )
            elif location.type == location_constants.TYPE_OSM:
                if not instance.id:  # skip these checks on update
                    for LOCATION_FIELD in instance.DUPLICATE_LOCATION_FIELDS:
                        location_field_value = getattr(
                            instance.location, LOCATION_FIELD.replace("location_", "")
                        )
                        if location_field_value:
                            price_field_value = getattr(instance, LOCATION_FIELD)
                            if str(location_field_value) != str(price_field_value):
                                utils.add_validation_error(
                                    errors,
                                    "location",
                                    f"Location {LOCATION_FIELD} ({location_field_value}) does not match the price {LOCATION_FIELD} ({price_field_value})",
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


def validate_price_proof_rules(instance):
    """
    - proof must exist and belong to the price owner
    - some proof fields should match the price fields (on create)
    - receipt_quantity can only be set for receipts (default to 1)
    """
    errors = dict()
    if instance.proof_id:
        proof = None
        from open_prices.proofs.models import Proof

        try:
            proof = Proof.objects.get(id=instance.proof_id)
        except Proof.DoesNotExist:
            utils.add_validation_error(
                errors,
                "proof",
                "Proof not found",
            )
        if proof:
            if (
                proof.owner != instance.owner
                and proof.type
                not in proof_constants.TYPE_GROUP_ALLOW_ANY_USER_PRICE_ADD_LIST
            ):
                utils.add_validation_error(
                    errors,
                    "proof",
                    f"Proof does not belong to the current user. Adding a price to a proof a user does not own is only allowed for {proof_constants.TYPE_GROUP_ALLOW_ANY_USER_PRICE_ADD_LIST} proofs",
                )
            if not instance.id:  # skip these checks on update
                if proof.type in proof_constants.TYPE_GROUP_SINGLE_SHOP_LIST:
                    for PROOF_FIELD in instance.DUPLICATE_PROOF_FIELDS:
                        proof_field_value = getattr(proof, PROOF_FIELD)
                        if proof_field_value:
                            price_field_value = getattr(instance, PROOF_FIELD)
                            if str(proof_field_value) != str(price_field_value):
                                utils.add_validation_error(
                                    errors,
                                    "proof",
                                    f"Proof {PROOF_FIELD} ({proof_field_value}) does not match the price {PROOF_FIELD} ({price_field_value})",
                                )
            if proof.type in proof_constants.TYPE_GROUP_CONSUMPTION_LIST:
                if not instance.receipt_quantity:
                    instance.receipt_quantity = 1
            else:
                if instance.receipt_quantity is not None:
                    utils.add_validation_error(
                        errors,
                        "receipt_quantity",
                        f"Can only be set if proof type in {proof_constants.TYPE_GROUP_CONSUMPTION_LIST}",
                    )
    return errors
