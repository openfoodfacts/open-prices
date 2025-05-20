from django.db import models
from django.utils import timezone
from solo.models import SingletonModel

from open_prices.common import constants


class TotalStats(SingletonModel):
    PRICE_COUNT_FIELDS = [
        "price_count",
        "price_type_product_code_count",
        "price_type_category_tag_count",
        "price_with_discount_count",
        "price_currency_count",
        "price_year_count",
        "price_location_country_count",
        "price_kind_community_count",
        "price_kind_consumption_count",
        "price_source_web_count",
        "price_source_mobile_count",
        "price_source_api_count",
        "price_source_other_count",
        "price_in_challenge_count",
    ]
    PRODUCT_COUNT_FIELDS = [
        "product_count",
        "product_source_off_count",
        "product_source_obf_count",
        "product_source_opff_count",
        "product_source_opf_count",
        "product_with_price_count",
        "product_source_off_with_price_count",
        "product_source_obf_with_price_count",
        "product_source_opff_with_price_count",
        "product_source_opf_with_price_count",
    ]
    LOCATION_COUNT_FIELDS = [
        "location_count",
        "location_with_price_count",
        "location_type_osm_count",
        "location_type_online_count",
        "location_type_osm_country_count",
    ]
    PROOF_COUNT_FIELDS = [
        "proof_count",
        "proof_with_price_count",
        "proof_type_price_tag_count",
        "proof_type_receipt_count",
        "proof_type_gdpr_request_count",
        "proof_type_shop_import_count",
        "proof_kind_community_count",
        "proof_kind_consumption_count",
        "proof_source_web_count",
        "proof_source_mobile_count",
        "proof_source_api_count",
        "proof_source_other_count",
        "proof_in_challenge_count",
    ]
    PRICE_TAG_COUNT_FIELDS = [
        "price_tag_count",
        "price_tag_status_unknown_count",
        "price_tag_status_linked_to_price_count",
    ]
    USER_COUNT_FIELDS = ["user_count", "user_with_price_count"]
    CHALLENGE_COUNT_FIELDS = ["challenge_count"]
    COUNT_FIELDS = (
        PRICE_COUNT_FIELDS
        + PRODUCT_COUNT_FIELDS
        + LOCATION_COUNT_FIELDS
        + PROOF_COUNT_FIELDS
        + PRICE_TAG_COUNT_FIELDS
        + USER_COUNT_FIELDS
        + CHALLENGE_COUNT_FIELDS
    )

    price_count = models.PositiveIntegerField(default=0)
    price_type_product_code_count = models.PositiveIntegerField(default=0)
    price_type_category_tag_count = models.PositiveIntegerField(default=0)
    price_with_discount_count = models.PositiveIntegerField(default=0)
    price_currency_count = models.PositiveIntegerField(default=0)
    price_year_count = models.PositiveIntegerField(default=0)
    price_location_country_count = models.PositiveIntegerField(default=0)
    price_kind_community_count = models.PositiveIntegerField(default=0)
    price_kind_consumption_count = models.PositiveIntegerField(default=0)
    price_source_web_count = models.PositiveIntegerField(default=0)
    price_source_mobile_count = models.PositiveIntegerField(default=0)
    price_source_api_count = models.PositiveIntegerField(default=0)
    price_source_other_count = models.PositiveIntegerField(default=0)
    price_in_challenge_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    product_source_off_count = models.PositiveIntegerField(default=0)
    product_source_obf_count = models.PositiveIntegerField(default=0)
    product_source_opff_count = models.PositiveIntegerField(default=0)
    product_source_opf_count = models.PositiveIntegerField(default=0)
    product_with_price_count = models.PositiveIntegerField(default=0)
    product_source_off_with_price_count = models.PositiveIntegerField(default=0)
    product_source_obf_with_price_count = models.PositiveIntegerField(default=0)
    product_source_opff_with_price_count = models.PositiveIntegerField(default=0)
    product_source_opf_with_price_count = models.PositiveIntegerField(default=0)
    location_count = models.PositiveIntegerField(default=0)
    location_with_price_count = models.PositiveIntegerField(default=0)
    location_type_osm_count = models.PositiveIntegerField(default=0)
    location_type_online_count = models.PositiveIntegerField(default=0)
    location_type_osm_country_count = models.PositiveIntegerField(default=0)
    proof_count = models.PositiveIntegerField(default=0)
    proof_with_price_count = models.PositiveIntegerField(default=0)
    proof_type_price_tag_count = models.PositiveIntegerField(default=0)
    proof_type_receipt_count = models.PositiveIntegerField(default=0)
    proof_type_gdpr_request_count = models.PositiveIntegerField(default=0)
    proof_type_shop_import_count = models.PositiveIntegerField(default=0)
    proof_kind_community_count = models.PositiveIntegerField(default=0)
    proof_kind_consumption_count = models.PositiveIntegerField(default=0)
    proof_source_web_count = models.PositiveIntegerField(default=0)
    proof_source_mobile_count = models.PositiveIntegerField(default=0)
    proof_source_api_count = models.PositiveIntegerField(default=0)
    proof_source_other_count = models.PositiveIntegerField(default=0)
    proof_in_challenge_count = models.PositiveIntegerField(default=0)
    price_tag_count = models.PositiveIntegerField(default=0)
    price_tag_status_unknown_count = models.PositiveIntegerField(default=0)
    price_tag_status_linked_to_price_count = models.PositiveIntegerField(default=0)
    user_count = models.PositiveIntegerField(default=0)
    user_with_price_count = models.PositiveIntegerField(default=0)
    challenge_count = models.PositiveIntegerField(default=0)

    # Ideas
    # - price count per discount type
    # - ?

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Total Stats"

    def update_price_stats(self):
        from open_prices.prices.models import Price

        self.price_count = Price.objects.count()
        self.price_type_product_code_count = Price.objects.filter(
            product_code__isnull=False
        ).count()
        self.price_type_category_tag_count = Price.objects.filter(
            category_tag__isnull=False
        ).count()
        self.price_with_discount_count = Price.objects.has_discount().count()
        self.price_currency_count = (
            Price.objects.values_list("currency", flat=True).distinct().count()
        )
        self.price_year_count = (
            Price.objects.with_extra_fields()
            .values_list("date_year_annotated", flat=True)
            .distinct()
            .count()
        )
        self.price_location_country_count = (
            Price.objects.select_related("location")
            .values_list("location__osm_address_country", flat=True)
            .distinct()
            .count()
        )
        self.price_kind_community_count = Price.objects.has_kind_community().count()
        self.price_kind_consumption_count = Price.objects.has_kind_consumption().count()
        for source in constants.SOURCE_LIST:
            setattr(
                self,
                f"price_source_{source.lower()}_count",
                Price.objects.with_extra_fields()
                .filter(source_annotated=source)
                .count(),
            )
        self.price_in_challenge_count = Price.objects.filter(
            tags__icontains="challenge"
        ).count()
        self.save(update_fields=self.PRICE_COUNT_FIELDS + ["updated"])

    def update_product_stats(self):
        from open_prices.products import constants as product_constants
        from open_prices.products.models import Product

        self.product_count = Product.objects.count()
        self.product_with_price_count = Product.objects.has_prices().count()
        # self.product_with_price_count = User.objects.values_list("product_id", flat=True).distinct().count()  # noqa
        for source in product_constants.SOURCE_LIST:
            setattr(
                self,
                f"product_source_{source.value}_count",
                Product.objects.filter(source=source.value).count(),
            )
            setattr(
                self,
                f"product_source_{source.value}_with_price_count",
                Product.objects.filter(source=source.value).has_prices().count(),
            )
        self.save(update_fields=self.PRODUCT_COUNT_FIELDS + ["updated"])

    def update_location_stats(self):
        from open_prices.locations.models import Location

        self.location_count = Location.objects.count()
        self.location_with_price_count = Location.objects.has_prices().count()
        # self.location_with_price_count = User.objects.values_list("location_id", flat=True).distinct().count()  # noqa
        self.location_type_osm_count = Location.objects.has_type_osm().count()
        self.location_type_online_count = Location.objects.has_type_online().count()
        self.location_type_osm_country_count = (
            Location.objects.has_type_osm()
            .values_list("osm_address_country", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=self.LOCATION_COUNT_FIELDS + ["updated"])

    def update_proof_stats(self):
        from open_prices.proofs.models import Proof

        self.proof_count = Proof.objects.count()
        self.proof_with_price_count = Proof.objects.has_prices().count()
        # self.proof_with_price_count = User.objects.values_list("proof_id", flat=True).distinct().count()  # noqa
        self.proof_type_price_tag_count = Proof.objects.has_type_price_tag().count()
        self.proof_type_receipt_count = Proof.objects.has_type_receipt().count()
        self.proof_type_gdpr_request_count = (
            Proof.objects.has_type_gdpr_request().count()
        )
        self.proof_type_shop_import_count = Proof.objects.has_type_shop_import().count()
        self.proof_kind_community_count = Proof.objects.has_kind_community().count()
        self.proof_kind_consumption_count = Proof.objects.has_kind_consumption().count()
        for source in constants.SOURCE_LIST:
            setattr(
                self,
                f"proof_source_{source.lower()}_count",
                Proof.objects.with_extra_fields()
                .filter(source_annotated=source)
                .count(),
            )
        self.proof_in_challenge_count = Proof.objects.filter(
            tags__icontains="challenge"
        ).count()
        self.save(update_fields=self.PROOF_COUNT_FIELDS + ["updated"])

    def update_price_tag_stats(self):
        from open_prices.proofs.models import PriceTag

        self.price_tag_count = PriceTag.objects.count()
        self.price_tag_status_unknown_count = PriceTag.objects.status_unknown().count()
        self.price_tag_status_linked_to_price_count = (
            PriceTag.objects.status_linked_to_price().count()
        )
        self.save(update_fields=self.PRICE_TAG_COUNT_FIELDS + ["updated"])

    def update_user_stats(self):
        from open_prices.users.models import User

        self.user_count = User.objects.count()
        self.user_with_price_count = User.objects.has_prices().count()
        # self.user_with_price_count = User.objects.values_list("owner", flat=True).distinct().count()  # noqa
        self.save(update_fields=self.USER_COUNT_FIELDS + ["updated"])

    def update_challenge_stats(self):
        from open_prices.challenges.models import Challenge

        self.challenge_count = Challenge.objects.published().count()
        self.save(update_fields=self.CHALLENGE_COUNT_FIELDS + ["updated"])
