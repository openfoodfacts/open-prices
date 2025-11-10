from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from open_prices.common import utils
from open_prices.moderation import validators as moderation_validators


class FlagReason(models.TextChoices):
    WRONG_TYPE = "WRONG_TYPE", "Wrong type"
    WRONG_PRICE_VALUE = "WRONG_PRICE_VALUE", "Wrong price value"
    WRONG_CURRENCY = "WRONG_CURRENCY", "Wrong currency"
    WRONG_PRODUCT = "WRONG_PRODUCT", "Wrong product"
    WRONG_LOCATION = "WRONG_LOCATION", "Wrong location"
    WRONG_DATE = "WRONG_DATE", "Wrong date"
    OTHER = "OTHER", "Other"


class FlagStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class Flag(models.Model):
    CREATE_FIELDS = [
        # object_id, owner & source: set via the request
        "reason",
        "comment",
        # "status"  # default
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    reason = models.CharField(max_length=20, choices=FlagReason.choices)
    comment = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=FlagStatus.choices,
        default=FlagStatus.OPEN,
    )
    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        verbose_name = "Flag"
        verbose_name_plural = "Flags"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = utils.merge_validation_errors(
            moderation_validators.validate_flag_models(self),
        )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        - run validations
        """
        self.full_clean()
        super().save(*args, **kwargs)
