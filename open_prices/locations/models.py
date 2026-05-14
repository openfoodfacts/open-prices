import math

from django.conf import settings
from django.core.validators import ValidationError
from django.db import models
from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Q,
    UniqueConstraint,
    Value,
    signals,
)
from django.db.models.functions import ACos, Cos, Radians, Sin
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task

from open_prices.common import utils
from open_prices.common.utils import truncate_decimal
from open_prices.locations import constants as location_constants
from open_prices.locations import utils as location_utils
from open_prices.locations import validators as location_validators


class LocationQuerySet(models.QuerySet):
    def has_type_osm(self):
        return self.filter(type=location_constants.TYPE_OSM)

    def has_type_online(self):
        return self.filter(type=location_constants.TYPE_ONLINE)

    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_stats(self):
        return self.prefetch_related("prices").annotate(
            price_count_annotated=Count("prices", distinct=True)
        )

    def calculate_field_distinct_count(self, field_name: str):
        return (
            self.exclude(**{f"{field_name}__isnull": True})
            .values(field_name)
            .distinct()
            .count()
        )

    def nearby(self, center_lat: float, center_lon: float, radius_km: float):
        # Earth's mean radius in kilometers, used for haversine distance calculations
        earth_radius_km = 6371.0
        # Approximate kilometers per degree of latitude (and longitude at the equator)
        km_per_degree = 111.32
        # Tolerance used to detect pole latitudes where cos(lat) is effectively zero
        pole_cos_tolerance = 1e-12
        # Full longitude span from center to edge when bounding at poles
        max_longitude_delta_degrees = 180.0

        # Bounding box pre-filter to reduce the number of rows for the
        # more expensive haversine calculation.
        delta_lat = radius_km / km_per_degree
        if radius_km == 0:
            delta_lon = 0.0
        else:
            cos_center_lat = math.cos(math.radians(center_lat))
            # At the poles, longitude is undefined and cos(lat) is 0.
            # Use full longitude span to avoid division by zero.
            if math.isclose(cos_center_lat, 0.0, abs_tol=pole_cos_tolerance):
                delta_lon = max_longitude_delta_degrees
            else:
                delta_lon = radius_km / (km_per_degree * cos_center_lat)

        center_lat_rad = math.radians(center_lat)
        center_lon_rad = math.radians(center_lon)

        # Haversine distance annotation (spherical law of cosines form).
        # d = R * acos(sin(φ1)*sin(φ2) + cos(φ1)*cos(φ2)*cos(Δλ))
        distance_expr = ExpressionWrapper(
            Value(earth_radius_km)
            * ACos(
                Sin(Value(center_lat_rad)) * Sin(Radians(F("osm_lat")))
                + Cos(Value(center_lat_rad))
                * Cos(Radians(F("osm_lat")))
                * Cos(Radians(F("osm_lon")) - Value(center_lon_rad))
            ),
            output_field=FloatField(),
        )

        return (
            self.filter(
                type=location_constants.TYPE_OSM,
                osm_lat__isnull=False,
                osm_lon__isnull=False,
                osm_lat__gte=center_lat - delta_lat,
                osm_lat__lte=center_lat + delta_lat,
                osm_lon__gte=center_lon - delta_lon,
                osm_lon__lte=center_lon + delta_lon,
            )
            .annotate(distance_km=distance_expr)
            .filter(distance_km__lte=radius_km)
            .order_by("distance_km", "id")
        )


class Location(models.Model):
    CREATE_FIELDS = ["type", "osm_id", "osm_type", "website_url"]
    LAT_LON_DECIMAL_FIELDS = ["osm_lat", "osm_lon"]
    URL_FIELDS = ["website_url"]
    COUNT_FIELDS = ["price_count", "user_count", "product_count", "proof_count"]
    TYPE_OSM_MANDATORY_FIELDS = ["osm_id", "osm_type"]
    TYPE_OSM_OPTIONAL_FIELDS = [
        "osm_name",
        "osm_display_name",
        "osm_tag_key",
        "osm_tag_value",
        "osm_brand",
        "osm_address_postcode",
        "osm_address_city",
        "osm_address_country",
        "osm_address_country_code",
        "osm_lat",
        "osm_lon",
        "osm_version",
    ]
    TYPE_ONLINE_MANDATORY_FIELDS = ["website_url"]

    type = models.CharField(max_length=20, choices=location_constants.TYPE_CHOICES)

    # type OSM
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
    osm_brand = models.CharField(blank=True, null=True)
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
    osm_version = models.PositiveIntegerField(blank=True, null=True)

    # type ONLINE
    website_url = models.URLField(blank=True, null=True)

    # denormalized counts (updated with signals and/or cronjobs)
    price_count = models.PositiveIntegerField(default=0)
    user_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    proof_count = models.PositiveIntegerField(default=0)

    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(LocationQuerySet)()

    class Meta:
        db_table = "locations"
        constraints = [
            UniqueConstraint(
                name=location_constants.TYPE_OSM_UNIQUE_CONSTRAINT_NAME,
                fields=["osm_id", "osm_type"],
                condition=Q(type=location_constants.TYPE_OSM),
            ),
            UniqueConstraint(
                name=location_constants.TYPE_ONLINE_UNIQUE_CONSTRAINT_NAME,
                fields=["website_url"],
                condition=Q(type=location_constants.TYPE_ONLINE),
            ),
        ]
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
                url = getattr(self, field_name)
                # add https:// if missing
                url = utils.url_add_missing_https(url)
                # keep only the domain
                url = utils.url_keep_only_domain(url)
                setattr(self, field_name, url)

    def clean(self, *args, **kwargs):
        # store all ValidationError in a dict
        validation_errors = utils.merge_validation_errors(
            location_validators.validate_location_type_osm_rules(self),
            location_validators.validate_location_type_online_rules(self),
        )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        - OSM: cleanup lat/lon fields
        - ONLINE: cleanup URL fields
        - run validations
        """
        if self.type == location_constants.TYPE_OSM:
            self.truncate_lat_lon()
        elif self.type == location_constants.TYPE_ONLINE:
            self.cleanup_url()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_type_osm(self):
        return self.type == location_constants.TYPE_OSM

    @property
    def is_type_online(self):
        return self.type == location_constants.TYPE_ONLINE

    @property
    def osm_brand_logo_url(self):
        if self.is_type_osm and self.osm_brand:
            return location_utils.get_brand_logo_url(self.osm_brand)
        return None

    def update_price_count(self):
        self.price_count = self.prices.count()
        self.save(update_fields=["price_count"])

    def update_user_count(self):
        from open_prices.proofs.models import Proof

        self.user_count = Proof.objects.filter(
            location=self
        ).calculate_field_distinct_count("owner")
        self.save(update_fields=["user_count"])

    def update_product_count(self):
        from open_prices.prices.models import Price

        self.product_count = Price.objects.filter(
            location=self
        ).calculate_field_distinct_count("product_id")
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
