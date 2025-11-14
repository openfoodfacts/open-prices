from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


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
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
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
