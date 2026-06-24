from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone

from open_prices.badges import constants as badge_constants
from open_prices.users.models import User


class Badge(models.Model):
    COUNT_FIELDS = ("user_count",)
    META_FIELDS = ("created", "updated")

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

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

    @classmethod
    def update_task(cls):
        """
        1. Give badges to users based on their count fields
        2. Update badge field counts
        """
        for badge in cls.objects.all():
            badge.update_user_badges()
            badge.update_user_count()

    def user_has_achieved(self, user: User) -> bool:
        """
        Examples:
        - user.price_count = 10 & badge.metric = "price_count" & badge.threshold = 5 => True
        - user.price_count = 10 & badge.metric = "price_count" & badge.threshold = 50 => False
        """
        return getattr(user, self.metric, 0) >= self.threshold

    def update_user_badges(self):
        user_badge_qs = User.objects.filter(**{f"{self.metric}__gte": self.threshold})
        UserBadge.objects.bulk_create(
            [UserBadge(user=user, badge=self) for user in user_badge_qs],
            ignore_conflicts=True,
        )

    def update_user_count(self):
        self.user_count = self.user_badges.count()
        self.save(update_fields=["user_count"])


class UserBadge(models.Model):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="user_badges"
    )
    badge = models.ForeignKey(
        Badge, on_delete=models.CASCADE, related_name="user_badges"
    )
    achieved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"
        constraints = [
            UniqueConstraint(
                fields=["user", "badge"], name="unique_user_badge_constraint"
            )
        ]

    def __str__(self):
        return f"{self.badge} - {self.user}"
