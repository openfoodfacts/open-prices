from django.db import models
from django.utils import timezone

from open_prices.badges import constants as badge_constants


class Badge(models.Model):
    COUNT_FIELDS = ("user_count",)
    META_FIELDS = ("created", "updated")

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    metric = models.CharField(max_length=40, choices=badge_constants.METRIC_CHOICES)
    threshold = models.PositiveIntegerField()

    user_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"

    def __str__(self):
        return self.name

    def user_has_achieved(self, user):
        """
        Examples:
        - user.price_count = 10, badge.metric = "price_count", badge.threshold = 5 => True
        - user.price_count = 10, badge.metric = "price_count", badge.threshold = 50 => False
        """
        return getattr(user, self.metric, 0) >= self.threshold
