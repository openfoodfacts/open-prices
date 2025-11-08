from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from open_prices.moderation import constants as moderation_constants


class Flag(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    reason = models.CharField(
        max_length=20, choices=moderation_constants.REASON_CHOICES
    )
    comment = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=moderation_constants.STATUS_CHOICES,
        default=moderation_constants.STATUS_OPEN,
    )
    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
