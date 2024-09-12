from django.db import models
from django.utils import timezone


class UserQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)


class User(models.Model):
    SERIALIZED_FIELDS = ["user_id", "price_count", "location_count"]

    user_id = models.CharField(primary_key=True)

    is_moderator = models.BooleanField(default=False)

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    location_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    # updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(UserQuerySet)()

    class Meta:
        # managed = False
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def is_authenticated(self):
        return True

    def update_price_count(self):
        from open_prices.prices.models import Price

        self.price_count = Price.objects.filter(owner=self).count()
        self.save(update_fields=["price_count"])

    def update_location_count(self):
        from open_prices.prices.models import Price

        self.location_count = (
            Price.objects.filter(owner=self.user_id)
            .values_list("location_id", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["location_count"])


class Session(models.Model):
    user = models.ForeignKey(
        "users.User", on_delete=models.DO_NOTHING, related_name="sessions"
    )
    token = models.CharField(unique=True)

    created = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = "sessions"
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
