from django.db import models
from django.db.models import F, Func
from django.db.models.functions import ExtractYear
from django.utils import timezone


class UserQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)


class User(models.Model):
    PRICE_COUNT_FIELDS = [
        "price_count",
        "price_type_product_count",
        "price_type_category_count",
        "price_kind_community_count",
        "price_kind_consumption_count",
        "price_in_proof_owned_count",
        "price_in_proof_not_owned_count",
        "price_not_owned_in_proof_owned_count",
    ]
    PROOF_COUNT_FIELDS = [
        "proof_count",
        "proof_kind_community_count",
        "proof_kind_consumption_count",
    ]
    LOCATION_COUNT_FIELDS = [
        "location_count",
        "location_type_osm_country_count",
    ]
    PRODUCT_COUNT_FIELDS = [
        "product_count",
    ]
    OTHER_COUNT_FIELDS = [
        "currency_count",
        "year_count",
        "challenge_count",
    ]
    COUNT_FIELDS = (
        PRICE_COUNT_FIELDS
        + PROOF_COUNT_FIELDS
        + LOCATION_COUNT_FIELDS
        + PRODUCT_COUNT_FIELDS
        + OTHER_COUNT_FIELDS
    )
    SERIALIZED_FIELDS = [
        "user_id",
    ] + COUNT_FIELDS

    user_id = models.CharField(primary_key=True)

    is_moderator = models.BooleanField(default=False)

    # denormalized counts (updated with signals and/or cronjobs)
    price_count = models.PositiveIntegerField(default=0)
    price_type_product_count = models.PositiveIntegerField(default=0)
    price_type_category_count = models.PositiveIntegerField(default=0)
    price_kind_community_count = models.PositiveIntegerField(default=0)
    price_kind_consumption_count = models.PositiveIntegerField(default=0)
    price_in_proof_owned_count = models.PositiveIntegerField(default=0)
    price_in_proof_not_owned_count = models.PositiveIntegerField(default=0)
    price_not_owned_in_proof_owned_count = models.PositiveIntegerField(default=0)
    location_count = models.PositiveIntegerField(default=0)
    location_type_osm_country_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    proof_count = models.PositiveIntegerField(default=0)
    proof_kind_community_count = models.PositiveIntegerField(default=0)
    proof_kind_consumption_count = models.PositiveIntegerField(default=0)
    currency_count = models.PositiveIntegerField(default=0)
    year_count = models.PositiveIntegerField(default=0)
    challenge_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    # updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(UserQuerySet)()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def is_authenticated(self):
        return True

    def update_price_count(self):
        from open_prices.prices.models import Price

        self.price_count = Price.objects.filter(owner=self.user_id).count()
        self.price_type_product_count = (
            Price.objects.filter(owner=self.user_id).has_type_product().count()
        )
        self.price_type_category_count = (
            Price.objects.filter(owner=self.user_id).has_type_category().count()
        )
        self.price_kind_community_count = (
            Price.objects.filter(owner=self.user_id).has_kind_community().count()
        )
        self.price_kind_consumption_count = (
            Price.objects.filter(owner=self.user_id).has_kind_consumption().count()
        )
        self.price_in_proof_owned_count = (
            Price.objects.select_related("proof")
            .filter(owner=self.user_id)
            .filter(proof__owner=self.user_id)
            .calculate_field_distinct_count("id")
        )
        self.price_in_proof_not_owned_count = (
            Price.objects.select_related("proof")
            .filter(owner=self.user_id)
            .exclude(proof__owner=self.user_id)
            .calculate_field_distinct_count("id")
        )
        self.price_not_owned_in_proof_owned_count = (
            Price.objects.select_related("proof")
            .exclude(owner=self.user_id)
            .filter(proof__owner=self.user_id)
            .calculate_field_distinct_count("id")
        )
        self.save(update_fields=self.PRICE_COUNT_FIELDS)

    def update_location_count(self):
        from open_prices.locations import constants as location_constants
        from open_prices.proofs.models import Proof

        self.location_count = Proof.objects.filter(
            owner=self.user_id, location_id__isnull=False
        ).calculate_field_distinct_count("location_id")
        self.location_type_osm_country_count = (
            Proof.objects.select_related("location")
            .filter(
                owner=self.user_id,
                location_id__isnull=False,
                location__type=location_constants.TYPE_OSM,
            )
            .calculate_field_distinct_count("location__osm_address_country")
        )
        self.save(update_fields=self.LOCATION_COUNT_FIELDS)

    def update_product_count(self):
        from open_prices.prices.models import Price

        self.product_count = Price.objects.filter(
            owner=self.user_id, product_id__isnull=False
        ).calculate_field_distinct_count("product_id")
        self.save(update_fields=self.PRODUCT_COUNT_FIELDS)

    def update_proof_count(self):
        from open_prices.proofs.models import Proof

        self.proof_count = Proof.objects.filter(owner=self.user_id).count()
        self.proof_kind_community_count = (
            Proof.objects.filter(owner=self.user_id).has_kind_community().count()
        )
        self.proof_kind_consumption_count = (
            Proof.objects.filter(owner=self.user_id).has_kind_consumption().count()
        )
        self.save(update_fields=self.PROOF_COUNT_FIELDS)

    def update_other_count(self):
        from open_prices.challenges import constants as challenge_constants
        from open_prices.prices.models import Price
        from open_prices.proofs.models import Proof

        self.currency_count = (  # should we filter on proof with prices only?
            Proof.objects.filter(owner=self.user_id).calculate_field_distinct_count(
                "currency"
            )
        )
        self.year_count = (
            Proof.objects.filter(owner=self.user_id)
            .annotate(date_year_annotated=ExtractYear("date"))
            .calculate_field_distinct_count("date_year_annotated")
        )
        proof_in_challenge_tag_list = (
            Proof.objects.exclude(tags=[])
            .filter(
                owner=self.user_id,
                tags__icontains=challenge_constants.CHALLENGE_TAG_PREFIX,
            )
            .annotate(tags_unnest=Func(F("tags"), function="unnest"))
            .values_list("tags_unnest", flat=True)
            .distinct()
        )
        price_in_challenge_tag_list = (
            Price.objects.exclude(tags=[])
            .filter(
                owner=self.user_id,
                tags__icontains=challenge_constants.CHALLENGE_TAG_PREFIX,
            )
            .annotate(tags_unnest=Func(F("tags"), function="unnest"))
            .values_list("tags_unnest", flat=True)
            .distinct()
        )
        self.challenge_count = len(
            set(proof_in_challenge_tag_list) | set(price_in_challenge_tag_list)
        )
        self.save(update_fields=self.OTHER_COUNT_FIELDS)


class Session(models.Model):
    user = models.ForeignKey(
        "users.User", on_delete=models.DO_NOTHING, related_name="sessions"
    )
    token = models.CharField(unique=True)

    created = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "sessions"
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
