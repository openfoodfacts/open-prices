from open_prices.common import utils
from open_prices.moderation import constants as moderation_constants


def validate_flag_models(instance):
    """
    - restrict Flag to only certain models
    """
    errors = dict()

    if (
        instance.content_type.model
        not in moderation_constants.FLAG_ALLOWED_CONTENT_TYPE_LIST
    ):
        utils.add_validation_error(
            errors,
            "content_type",
            f"Supported models: {', '.join(moderation_constants.FLAG_ALLOWED_CONTENT_TYPE_LIST)}",
        )

    return errors
