from django.contrib.contenttypes.models import ContentType

from open_prices.common import utils


def validate_flag_models(instance):
    """
    - restrict Flag to only certain models: Price, Proof
    """
    errors = dict()

    allowed_models = [
        ContentType.objects.get(app_label="prices", model="price"),
        ContentType.objects.get(app_label="proofs", model="proof"),
    ]
    if instance.content_type not in allowed_models:
        utils.add_validation_error(
            errors, "content_type", "Supported models: Price, Proof"
        )

    return errors
