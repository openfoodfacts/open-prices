from django.conf import settings
from django.core.validators import ValidationError
from django.db import models
from django.db.models import Count, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task

from open_prices.common import utils
from open_prices.common.utils import truncate_decimal
from open_prices.locations import constants as location_constants


class LocationQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_stats(self):
        return self.annotate(price_count_annotated=Count("prices", distinct=True))


class Location(models.Model):
    CREATE_FIELDS = ["type", "osm_id", "osm_type", "website_url"]
    LAT_LON_DECIMAL_FIELDS = ["osm_lat", "osm_lon"]
    URL_FIELDS = ["website_url"]
    COUNT_FIELDS = ["price_count", "user_count", "product_count", "proof_count"]

    type = models.CharField(max_length=20, choices=location_constants.TYPE_CHOICES)

    # OSM
    osm_id = models.PositiveBigIntegerField(blank=True, null=True)
    osm_type = models.CharField(
        max_length=10,
        choices=location_constants.OSM_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    osm_name = models.CharField(blank=True, null=True)
    osm_display_name = models.CharField(blank=True, null=True)
    osm_tag_key = models.CharField(blank=True, null=True)
    osm_tag_value = models.CharField(blank=True, null=True)
    osm_address_postcode = models.CharField(blank=True, null=True)
    osm_address_city = models.CharField(blank=True, null=True)
    osm_address_country = models.CharField(blank=True, null=True)
    osm_address_country_code = models.CharField(blank=True, null=True)
    osm_lat = models.DecimalField(
        max_digits=11, decimal_places=7, blank=True, null=True
    )
    osm_lon = models.DecimalField(
        max_digits=11, decimal_places=7, blank=True, null=True
    )

    # WEBSITE
    website_url = models.URLField(blank=True, null=True)

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    user_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    product_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    proof_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(LocationQuerySet)()

    class Meta:
        # managed = False
        db_table = "locations"
        unique_together = ["osm_id", "osm_type"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def truncate_lat_lon(self):
        for field_name in self.LAT_LON_DECIMAL_FIELDS:
            if getattr(self, field_name) is not None:
                setattr(
                    self,
                    field_name,
                    truncate_decimal(getattr(self, field_name), max_decimal_places=7),
                )

    def cleanup_url(self):
        for field_name in self.URL_FIELDS:
            if getattr(self, field_name) is not None:
                if not getattr(self, field_name).startswith("https://"):
                    setattr(self, field_name, f"https://{getattr(self, field_name)}")

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # osm rules
        if self.type == location_constants.TYPE_OSM:
            if not self.osm_id:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "osm_id",
                    f"Should be set (type = {self.type})",
                )
            elif self.osm_id in [True, "true", "false", "none", "null"]:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "osm_id",
                    "Should not be a boolean or an invalid string",
                )
            if not self.osm_type:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "osm_type",
                    f"Should be set (type = {self.type})",
                )
            if self.website_url:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "website_url",
                    f"Should not be set (type = {self.type})",
                )
        # website rules
        elif self.type == location_constants.TYPE_WEBSITE:
            if not self.website_url:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "website_url",
                    f"Should be set (type = {self.type})",
                )
            if self.osm_id:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "osm_id",
                    f"Should not be set (type = {self.type})",
                )
            if self.osm_type:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "osm_type",
                    f"Should not be set (type = {self.type})",
                )

        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        - truncate decimal fields
        - run validations
        """
        if self.type == location_constants.TYPE_OSM:
            self.truncate_lat_lon()
        elif self.type == location_constants.TYPE_WEBSITE:
            self.cleanup_url()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_type_osm(self):
        return self.type == location_constants.TYPE_OSM

    @property
    def is_type_website(self):
        return self.type == location_constants.TYPE_WEBSITE

    def update_price_count(self):
        self.price_count = self.prices.count()
        self.save(update_fields=["price_count"])

    def update_user_count(self):
        from open_prices.prices.models import Price

        self.user_count = (
            Price.objects.filter(location=self, owner__isnull=False)
            .values_list("owner", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["user_count"])

    def update_product_count(self):
        from open_prices.prices.models import Price

        self.product_count = (
            Price.objects.filter(location=self, product_id__isnull=False)
            .values_list("product_id", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["product_count"])

    def update_proof_count(self):
        self.proof_count = self.proofs.count()
        self.save(update_fields=["proof_count"])


@receiver(signals.post_save, sender=Location)
def location_post_create_fetch_and_save_data_from_openstreetmap(
    sender, instance, created, **kwargs
):
    if not settings.TESTING:
        if instance.type == location_constants.TYPE_OSM:
            if created:
                async_task(
                    "open_prices.locations.tasks.fetch_and_save_data_from_openstreetmap",
                    instance,
                )
