from collections import Counter, defaultdict

from django.db import models
from django.db.models import Count, F, Func, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, ExtractYear
from django.utils import timezone

from open_prices.common.counts import bulk_update_counts, group_counts


class UserQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_badge_count(self):
        from open_prices.badges.models import UserBadge

        badge_count_subquery = (
            UserBadge.objects.filter(user=OuterRef("user_id"))
            .order_by()
            .values("user")
            .annotate(count=Count("id"))
            .values("count")
        )
        return self.annotate(
            badge_count_annotated=Coalesce(Subquery(badge_count_subquery), 0)
        )


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
        "proof_type_price_tag_count",
        "proof_type_receipt_count",
        "proof_type_gdpr_request_count",
        "proof_type_shop_import_count",
        "proof_kind_community_count",
        "proof_kind_consumption_count",
    ]
    LOCATION_COUNT_FIELDS = [
        "location_count",
        "location_type_osm_city_count",
        "location_type_osm_country_count",
    ]
    PRODUCT_COUNT_FIELDS = [
        "product_count",
    ]
    BADGE_COUNT_FIELDS = [
        "badge_count",
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
        + BADGE_COUNT_FIELDS
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
    location_type_osm_city_count = models.PositiveIntegerField(default=0)
    location_type_osm_country_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    proof_count = models.PositiveIntegerField(default=0)
    proof_type_price_tag_count = models.PositiveIntegerField(default=0)
    proof_type_receipt_count = models.PositiveIntegerField(default=0)
    proof_type_gdpr_request_count = models.PositiveIntegerField(default=0)
    proof_type_shop_import_count = models.PositiveIntegerField(default=0)
    proof_kind_community_count = models.PositiveIntegerField(default=0)
    proof_kind_consumption_count = models.PositiveIntegerField(default=0)
    currency_count = models.PositiveIntegerField(default=0)
    year_count = models.PositiveIntegerField(default=0)
    challenge_count = models.PositiveIntegerField(default=0)
    badge_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    # updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(UserQuerySet)()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    @classmethod
    def update_task(cls):
        """
        - Update user field counts (except badge_count)
        (same as the update_*_count() methods)
        - Counts are computed with 5 queries per batch of users,
        and only the users with changed counts are updated
        """
        from open_prices.challenges import constants as challenge_constants
        from open_prices.locations import constants as location_constants
        from open_prices.prices import constants as price_constants
        from open_prices.prices.models import Price
        from open_prices.proofs import constants as proof_constants
        from open_prices.proofs.models import Proof

        count_fields = [
            field for field in cls.COUNT_FIELDS if field not in cls.BADGE_COUNT_FIELDS
        ]

        def get_counts(user_ids):
            price_counts = group_counts(
                Price.objects.filter(owner__in=user_ids),
                "owner",
                price_count=Count("id"),
                price_type_product_count=Count(
                    "id", filter=Q(type=price_constants.TYPE_PRODUCT)
                ),
                price_type_category_count=Count(
                    "id", filter=Q(type=price_constants.TYPE_CATEGORY)
                ),
                price_owner_consumption_count=Count(
                    "id", filter=Q(proof__owner_consumption=True)
                ),
                price_kind_consumption_count=Count(
                    "id",
                    filter=Q(
                        proof__type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST,
                        proof__owner_consumption=True,
                    ),
                ),
                price_in_proof_owned_count=Count(
                    "id", filter=Q(proof__owner=F("owner"))
                ),
                product_count=Count("product_id", distinct=True),
            )
            price_in_proof_counts = group_counts(
                Price.objects.filter(proof__owner__in=user_ids),
                "proof__owner",
                price_in_proof_count=Count("id"),
            )
            proof_counts = group_counts(
                Proof.objects.filter(owner__in=user_ids),
                "owner",
                proof_count=Count("id"),
                proof_type_price_tag_count=Count(
                    "id", filter=Q(type=proof_constants.TYPE_PRICE_TAG)
                ),
                proof_type_receipt_count=Count(
                    "id", filter=Q(type=proof_constants.TYPE_RECEIPT)
                ),
                proof_type_gdpr_request_count=Count(
                    "id", filter=Q(type=proof_constants.TYPE_GDPR_REQUEST)
                ),
                proof_type_shop_import_count=Count(
                    "id", filter=Q(type=proof_constants.TYPE_SHOP_IMPORT)
                ),
                proof_owner_consumption_count=Count(
                    "id", filter=Q(owner_consumption=True)
                ),
                proof_kind_consumption_count=Count(
                    "id",
                    filter=Q(
                        type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST,
                        owner_consumption=True,
                    ),
                ),
                location_count=Count("location_id", distinct=True),
                location_type_osm_city_count=Count(
                    "location__osm_address_city",
                    distinct=True,
                    filter=Q(location__type=location_constants.TYPE_OSM),
                ),
                location_type_osm_country_count=Count(
                    "location__osm_address_country",
                    distinct=True,
                    filter=Q(location__type=location_constants.TYPE_OSM),
                ),
                currency_count=Count("currency", distinct=True),
                year_count=Count(ExtractYear("date"), distinct=True),
            )
            challenge_tags = defaultdict(set)
            for queryset in [
                Proof.objects.filter(owner__in=user_ids),
                Price.objects.filter(owner__in=user_ids),
            ]:
                for owner, tag in (
                    queryset.exclude(tags=[])
                    .filter(tags__icontains=challenge_constants.CHALLENGE_TAG_PREFIX)
                    .annotate(tags_unnest=Func(F("tags"), function="unnest"))
                    .values_list("owner", "tags_unnest")
                    .distinct()
                ):
                    challenge_tags[owner].add(tag)

            counts = dict()
            for user_id in user_ids:
                user_price_counts = price_counts.get(user_id, {})
                user_proof_counts = proof_counts.get(user_id, {})
                price_count = user_price_counts.get("price_count", 0)
                price_in_proof_owned_count = user_price_counts.get(
                    "price_in_proof_owned_count", 0
                )
                proof_count = user_proof_counts.get("proof_count", 0)
                counts[user_id] = {
                    **user_price_counts,
                    **user_proof_counts,
                    "price_kind_community_count": price_count
                    - user_price_counts.get("price_owner_consumption_count", 0),
                    "price_in_proof_not_owned_count": price_count
                    - price_in_proof_owned_count,
                    "price_not_owned_in_proof_owned_count": price_in_proof_counts.get(
                        user_id, {}
                    ).get("price_in_proof_count", 0)
                    - price_in_proof_owned_count,
                    "proof_kind_community_count": proof_count
                    - user_proof_counts.get("proof_owner_consumption_count", 0),
                    "challenge_count": len(challenge_tags[user_id]),
                }
            return counts

        return bulk_update_counts(cls.objects.all(), count_fields, get_counts)

    @classmethod
    def update_badge_count_task(cls):
        """
        - Update user badge_count field
        """
        cls.objects.with_badge_count().update(badge_count=F("badge_count_annotated"))

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
            owner=self.user_id
        ).calculate_field_distinct_count("location_id")
        # NOTE: we could count by distinct city+country in the future
        self.location_type_osm_city_count = (
            Proof.objects.select_related("location")
            .filter(
                owner=self.user_id,
                location_id__isnull=False,
                location__type=location_constants.TYPE_OSM,
            )
            .calculate_field_distinct_count("location__osm_address_city")
        )
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
            owner=self.user_id
        ).calculate_field_distinct_count("product_id")
        self.save(update_fields=self.PRODUCT_COUNT_FIELDS)

    def update_proof_count(self):
        from open_prices.proofs import constants as proof_constants
        from open_prices.proofs.models import Proof

        self.proof_count = Proof.objects.filter(owner=self.user_id).count()
        proof_count_per_type = Counter(
            Proof.objects.filter(owner=self.user_id).values_list("type", flat=True)
        )
        self.proof_type_price_tag_count = proof_count_per_type.get(
            proof_constants.TYPE_PRICE_TAG, 0
        )
        self.proof_type_receipt_count = proof_count_per_type.get(
            proof_constants.TYPE_RECEIPT, 0
        )
        self.proof_type_gdpr_request_count = proof_count_per_type.get(
            proof_constants.TYPE_GDPR_REQUEST, 0
        )
        self.proof_type_shop_import_count = proof_count_per_type.get(
            proof_constants.TYPE_SHOP_IMPORT, 0
        )
        self.proof_kind_community_count = (
            Proof.objects.filter(owner=self.user_id).has_kind_community().count()
        )
        self.proof_kind_consumption_count = (
            Proof.objects.filter(owner=self.user_id).has_kind_consumption().count()
        )
        self.save(update_fields=self.PROOF_COUNT_FIELDS)

    def update_badge_count(self):
        from open_prices.badges.models import UserBadge

        self.badge_count = UserBadge.objects.filter(user=self.user_id).count()
        self.save(update_fields=self.BADGE_COUNT_FIELDS)

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
