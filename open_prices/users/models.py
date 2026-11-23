from django.db import models
from django.db.models import Count, Exists, F, Func, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, ExtractYear
from django.utils import timezone

from open_prices.common.counts import (
    CountsQuerySetMixin,
    bulk_update_counts,
    update_counts,
)


class UserQuerySet(CountsQuerySetMixin, models.QuerySet):
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

    def with_counts(self):
        """
        All the COUNT_FIELDS, annotated as "<count field>_annotated"
        (except badge_count & challenge_count)
        """
        from open_prices.locations import constants as location_constants
        from open_prices.prices import constants as price_constants
        from open_prices.prices.models import Price
        from open_prices.proofs import constants as proof_constants
        from open_prices.proofs.models import Proof

        in_proof_owned = Q(proof__owner=F("owner"))
        is_location_type_osm = Q(location__type=location_constants.TYPE_OSM)
        return (
            self.annotate_counts(
                Price,
                "owner",
                {
                    "price_count": Count("id"),
                    "price_type_product_count": Count(
                        "id", filter=Q(type=price_constants.TYPE_PRODUCT)
                    ),
                    "price_type_category_count": Count(
                        "id", filter=Q(type=price_constants.TYPE_CATEGORY)
                    ),
                    "price_kind_community_count": Count(
                        "id", filter=~Q(proof__owner_consumption=True)
                    ),
                    "price_kind_consumption_count": Count(
                        "id",
                        filter=Q(
                            proof__type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST,
                            proof__owner_consumption=True,
                        ),
                    ),
                    "price_in_proof_owned_count": Count("id", filter=in_proof_owned),
                    "price_in_proof_not_owned_count": Count(
                        "id", filter=~in_proof_owned
                    ),
                    "product_count": Count("product_id", distinct=True),
                },
            )
            .annotate_counts(
                Price,
                "proof__owner",  # prices in the proofs of the user
                {
                    "price_not_owned_in_proof_owned_count": Count(
                        "id", filter=~in_proof_owned
                    ),
                },
            )
            .annotate_counts(
                Proof,  # drafts excluded
                "owner",
                {
                    "proof_count": Count("id"),
                    "proof_type_price_tag_count": Count(
                        "id", filter=Q(type=proof_constants.TYPE_PRICE_TAG)
                    ),
                    "proof_type_receipt_count": Count(
                        "id", filter=Q(type=proof_constants.TYPE_RECEIPT)
                    ),
                    "proof_type_gdpr_request_count": Count(
                        "id", filter=Q(type=proof_constants.TYPE_GDPR_REQUEST)
                    ),
                    "proof_type_shop_import_count": Count(
                        "id", filter=Q(type=proof_constants.TYPE_SHOP_IMPORT)
                    ),
                    "proof_kind_community_count": Count(
                        "id", filter=~Q(owner_consumption=True)
                    ),
                    "proof_kind_consumption_count": Count(
                        "id",
                        filter=Q(
                            type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST,
                            owner_consumption=True,
                        ),
                    ),
                    "location_count": Count("location_id", distinct=True),
                    # NOTE: we could count by distinct city+country in the future
                    "location_type_osm_city_count": Count(
                        "location__osm_address_city",
                        distinct=True,
                        filter=is_location_type_osm,
                    ),
                    "location_type_osm_country_count": Count(
                        "location__osm_address_country",
                        distinct=True,
                        filter=is_location_type_osm,
                    ),
                    # should we filter on proofs with prices only?
                    "currency_count": Count("currency", distinct=True),
                    "year_count": Count(ExtractYear("date"), distinct=True),
                },
            )
        )

    def with_challenge_tags(self):
        """
        Users with proofs or prices tagged with a challenge
        """
        from open_prices.challenges import constants as challenge_constants
        from open_prices.prices.models import Price
        from open_prices.proofs.models import Proof

        return self.filter(
            Q(
                Exists(
                    Proof.objects.filter(
                        owner=OuterRef("pk"),
                        tags__icontains=challenge_constants.CHALLENGE_TAG_PREFIX,
                    )
                )
            )
            | Q(
                Exists(
                    Price.objects.filter(
                        owner=OuterRef("pk"),
                        tags__icontains=challenge_constants.CHALLENGE_TAG_PREFIX,
                    )
                )
            )
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
    # the counts annotated by with_counts()
    ANNOTATED_COUNT_FIELDS = (
        PRICE_COUNT_FIELDS
        + PROOF_COUNT_FIELDS
        + LOCATION_COUNT_FIELDS
        + PRODUCT_COUNT_FIELDS
        + ["currency_count", "year_count"]
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
        - Only the users with changed counts are updated
        """
        bulk_update_counts(cls.objects.with_counts(), cls.ANNOTATED_COUNT_FIELDS)
        cls.bulk_update_challenge_count()

    @classmethod
    def bulk_update_challenge_count(cls):
        """
        challenge_count can't be annotated (unnest of the tags):
        computed user by user, for the users with challenge tags (or a stale count)
        """
        users_to_update = list()
        for user in cls.objects.filter(
            Q(challenge_count__gt=0) | Q(pk__in=cls.objects.with_challenge_tags())
        ):
            challenge_count = user.calculate_challenge_count()
            if user.challenge_count != challenge_count:
                user.challenge_count = challenge_count
                users_to_update.append(user)
        cls.objects.bulk_update(users_to_update, ["challenge_count"], batch_size=1000)

    @classmethod
    def update_badge_count_task(cls):
        """
        - Update user badge_count field
        """
        cls.objects.with_badge_count().update(badge_count=F("badge_count_annotated"))

    def is_authenticated(self):
        return True

    def update_counts(self):
        """
        Update all the count fields (except badge_count)
        """
        update_counts(self, self.ANNOTATED_COUNT_FIELDS)
        self.challenge_count = self.calculate_challenge_count()
        self.save(update_fields=["challenge_count"])

    def update_badge_count(self):
        from open_prices.badges.models import UserBadge

        self.badge_count = UserBadge.objects.filter(user=self.user_id).count()
        self.save(update_fields=self.BADGE_COUNT_FIELDS)

    def calculate_challenge_count(self):
        """
        Number of distinct tags of the user's proofs & prices tagged with
        a challenge
        """
        from open_prices.challenges import constants as challenge_constants
        from open_prices.prices.models import Price
        from open_prices.proofs.models import Proof

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
        return len(set(proof_in_challenge_tag_list) | set(price_in_challenge_tag_list))


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
