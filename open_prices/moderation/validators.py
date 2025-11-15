from django.contrib.contenttypes.models import ContentType

from open_prices.common import utils
from open_prices.moderation import constants as moderation_constants


def validate_flag_models(instance):
    """
    - restrict Flag to only certain models: Price, Proof
    """
    errors = dict()

    if instance.content_type not in ContentType.objects.filter(
        moderation_constants.FLAG_ALLOWED_CONTENT_TYPES_QUERY_LIST
    ):
        utils.add_validation_error(
            errors, "content_type", "Supported models: Price, Proof"
        )

    return errors
