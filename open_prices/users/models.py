from django.db import models
from django.utils import timezone

from open_prices.locations import constants as location_constants


class UserQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)


class User(models.Model):
    COUNT_FIELDS = [
        "price_count",
        "price_currency_count",
        "location_count",
        "location_type_osm_country_count",
        "product_count",
        "proof_count",
    ]
    SERIALIZED_FIELDS = [
        "user_id",
    ] + COUNT_FIELDS

    user_id = models.CharField(primary_key=True)

    is_moderator = models.BooleanField(default=False)

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    price_currency_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    location_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    location_type_osm_country_count = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    product_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    proof_count = models.PositiveIntegerField(default=0, blank=True, null=True)

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

        self.price_count = Price.objects.filter(owner=self.user_id).count()
        self.price_currency_count = (
            Price.objects.filter(owner=self.user_id)
            .values_list("currency", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["price_count", "price_currency_count"])

    def update_location_count(self):
        from open_prices.proofs.models import Proof

        self.location_count = (
            Proof.objects.filter(owner=self.user_id, location_id__isnull=False)
            .values_list("location_id", flat=True)
            .distinct()
            .count()
        )
        self.location_type_osm_country_count = (
            Proof.objects.select_related("location")
            .filter(
                owner=self.user_id,
                location_id__isnull=False,
                location__type=location_constants.TYPE_OSM,
            )
            .values_list("location__osm_address_country", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["location_count", "location_type_osm_country_count"])

    def update_product_count(self):
        from open_prices.prices.models import Price

        self.product_count = (
            Price.objects.filter(owner=self.user_id, product_id__isnull=False)
            .values_list("product_id", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["product_count"])

    def update_proof_count(self):
        from open_prices.proofs.models import Proof

        self.proof_count = Proof.objects.filter(owner=self.user_id).count()
        self.save(update_fields=["proof_count"])


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
