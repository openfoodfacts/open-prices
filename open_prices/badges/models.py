from django.db import models
from django.utils import timezone

from open_prices.badges import constants as badge_constants


class BadgeDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    metric = models.CharField(max_length=40, choices=badge_constants.METRIC_CHOICES)
    threshold = models.PositiveIntegerField()

    user_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Badge Definition"
        verbose_name_plural = "Badge Definitions"

    def __str__(self):
        return self.name
