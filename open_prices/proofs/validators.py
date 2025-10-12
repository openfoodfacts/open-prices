from open_prices.common import utils
from open_prices.proofs import constants as proof_constants


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
