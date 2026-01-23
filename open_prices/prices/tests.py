import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from freezegun import freeze_time
from simple_history.utils import bulk_update_with_history

from open_prices.challenges.factories import ChallengeFactory
from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof
from open_prices.users.factories import SessionFactory
from open_prices.users.models import User

PRODUCT_8001505005707 = {
    "code": "8001505005707",
    "product_name": "Nocciolata",
    "categories_tags": ["en:breakfasts", "en:spreads"],
    "labels_tags": ["en:no-gluten", "en:organic"],
    "brands_tags": ["rigoni-di-asiago"],
    "price_count": 15,
}

PRODUCT_8850187002197 = {
    "code": "8850187002197",
    "product_name": "Riz 20 kg",
    "categories_tags": ["en:rices"],
    "labels_tags": [],
    "brands_tags": ["royal-umbrella"],
    "price_count": 10,
}


class PriceQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_receipt = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, owner_consumption=True
        )
        PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            price=5,
            price_is_discounted=True,
            price_without_discount=10,
            product_name="",
        )
        PriceFactory(
            type=price_constants.TYPE_PRODUCT, price=8, source="Open Prices Web App"
        )
        PriceFactory(
            proof_id=cls.proof_receipt.id,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:apples",
            price_per=price_constants.PRICE_PER_UNIT,
            price=10,
            date="2024-01-01",
            tags=["challenge-1"],
            product_name="POMME VRAC",
        )

    def test_has_discount(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_discount().count(), 1)

    def test_exclude_discounted(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.exclude_discounted().count(), 2)

    def test_has_type_product(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_type_product().count(), 2)

    def test_has_type_category(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_type_category().count(), 1)

    def test_has_kind_community(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_kind_community().count(), 2)

    def test_has_kind_consumption(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_kind_consumption().count(), 1)

    def test_has_product_name(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_product_name().count(), 1)

    def with_extra_fields(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(
            Price.objects.with_extra_fields().filter(date_year_annotated=2024).count(),
            1,
        )
        self.assertEqual(
            Price.objects.with_extra_fields()
            .filter(source_annotated=constants.SOURCE_WEB)
            .count(),
            1,
        )

    def test_min(self):
        self.assertEqual(Price.objects.calculate_min(), 5)
        self.assertEqual(Price.objects.exclude_discounted().calculate_min(), 8)

    def test_max(self):
        self.assertEqual(Price.objects.calculate_max(), 10)
        self.assertEqual(Price.objects.exclude_discounted().calculate_max(), 10)

    def test_avg(self):
        self.assertEqual(Price.objects.calculate_avg(), Decimal("7.67"))
        self.assertEqual(Price.objects.exclude_discounted().calculate_avg(), 9)

    def test_calculate_stats(self):
        self.assertEqual(
            Price.objects.calculate_stats(),
            {
                "price__count": 3,
                "price__min": 5,
                "price__max": 10,
                "price__avg": Decimal("7.67"),
            },
        )
        self.assertEqual(
            Price.objects.exclude_discounted().calculate_stats(),
            {
                "price__count": 2,
                "price__min": 8,
                "price__max": 10,
                "price__avg": 9,
            },
        )

    def test_has_tag(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_tag("challenge-1").count(), 1)
        self.assertEqual(Price.objects.has_tag("unknown").count(), 0)


class PriceChallengeQuerySetAndPropertyAndSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = LocationFactory()
        cls.challenge_ongoing_with_category = ChallengeFactory(
            is_published=True,
            start_date="2024-12-30",
            end_date="2025-01-30",
            categories=["en:breakfasts"],
        )
        cls.challenge_ongoing_with_location = ChallengeFactory(
            is_published=True,
            start_date="2024-12-30",
            end_date="2025-01-30",
            categories=[],
            locations=[cls.location],
        )
        cls.product_8001505005707 = ProductFactory(
            **PRODUCT_8001505005707
        )  # in challenge
        cls.product_8850187002197 = ProductFactory(**PRODUCT_8850187002197)
        with freeze_time("2025-01-01"):  # during the challenge
            cls.price_11 = PriceFactory()
            cls.price_12 = PriceFactory(
                product_code="8001505005707",
                product=cls.product_8001505005707,
            )
            cls.price_13 = PriceFactory(
                product_code="8850187002197",
                product=cls.product_8850187002197,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
            )
            cls.price_14 = PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="en:breakfasts",
                price_per=price_constants.PRICE_PER_UNIT,
            )

        with freeze_time("2025-01-30 22:00:00"):  # last day of the challenge
            cls.price_21 = PriceFactory()
            cls.price_22 = PriceFactory(
                product_code="8001505005707",
                product=cls.product_8001505005707,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
            )
            cls.price_23 = PriceFactory(
                product_code="8850187002197", product=cls.product_8850187002197
            )

        with freeze_time("2025-02-01"):  # after the challenge
            cls.price_31 = PriceFactory()
            cls.price_32 = PriceFactory(
                product_code="8001505005707",
                product=cls.product_8001505005707,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
            )
            cls.price_33 = PriceFactory(
                product_code="8850187002197", product=cls.product_8850187002197
            )

    def test_in_challenge_queryset(self):
        self.assertEqual(Price.objects.count(), 10)
        self.assertEqual(
            Price.objects.in_challenge(self.challenge_ongoing_with_category).count(), 3
        )
        self.assertEqual(
            Price.objects.in_challenge(self.challenge_ongoing_with_location).count(), 2
        )

    def test_has_category_tag_property(self):
        for price in Price.objects.all():
            # challenge_ongoing_with_category
            if price in [self.price_12, self.price_14, self.price_22, self.price_32]:
                self.assertEqual(
                    price.has_category_tag(
                        self.challenge_ongoing_with_category.categories
                    ),
                    True,
                )
            else:
                self.assertEqual(
                    price.has_category_tag(
                        self.challenge_ongoing_with_category.categories
                    ),
                    False,
                )
            # challenge_ongoing_with_location
            self.assertEqual(
                price.has_category_tag(self.challenge_ongoing_with_location.categories),
                False,
            )

    def test_has_location_property(self):
        for price in Price.objects.all():
            # challenge_ongoing_with_category
            self.assertEqual(
                price.has_location(
                    self.challenge_ongoing_with_category.location_id_list()
                ),
                False,
            )
            # challenge_ongoing_with_location
            if price in [self.price_13, self.price_22, self.price_32]:
                self.assertEqual(
                    price.has_location(
                        self.challenge_ongoing_with_location.location_id_list()
                    ),
                    True,
                )
            else:
                self.assertEqual(
                    price.has_location(
                        self.challenge_ongoing_with_location.location_id_list()
                    ),
                    False,
                )

    def test_in_challenge_property(self):
        for price in Price.objects.all():
            # challenge_ongoing_with_category
            if price in [self.price_12, self.price_14, self.price_22]:
                self.assertEqual(
                    price.in_challenge(self.challenge_ongoing_with_category), True
                )
            else:
                self.assertEqual(
                    price.in_challenge(self.challenge_ongoing_with_category), False
                )
            # challenge_ongoing_with_location
            if price in [self.price_13, self.price_22]:
                self.assertEqual(
                    price.in_challenge(self.challenge_ongoing_with_location), True
                )
            else:
                self.assertEqual(
                    price.in_challenge(self.challenge_ongoing_with_location), False
                )

    def test_on_create_signal(self):
        for price in Price.objects.all():  # refresh_from_db
            # challenge_ongoing_with_category
            if price in [self.price_12, self.price_14, self.price_22]:
                self.assertIn(
                    f"challenge-{self.challenge_ongoing_with_category.id}", price.tags
                )
            else:
                self.assertNotIn(
                    f"challenge-{self.challenge_ongoing_with_category.id}", price.tags
                )
            # challenge_ongoing_with_location
            if price in [self.price_13, self.price_22]:
                self.assertIn(
                    f"challenge-{self.challenge_ongoing_with_location.id}", price.tags
                )
            else:
                self.assertNotIn(
                    f"challenge-{self.challenge_ongoing_with_location.id}", price.tags
                )


class PriceModelSaveTest(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_price_product_validation(self):
        for PRODUCT_CODE_OK in ["8001505005707", 5]:
            PriceFactory(product_code=PRODUCT_CODE_OK)
        for PRODUCT_CODE_NOT_OK in ["...", 5.0, "8001505005707?", True, "None"]:
            self.assertRaises(
                ValidationError, PriceFactory, product_code=PRODUCT_CODE_NOT_OK
            )

    def test_product_code_normalization_on_save(self):
        # barcode of length < 8 gets padded to 8
        price = PriceFactory(product_code="4567")
        self.assertEqual(price.product_code, "00004567")
        # EAN8 without leading 0 stays the same
        price = PriceFactory(product_code="51234567")
        self.assertEqual(price.product_code, "51234567")
        # barcode of length 12 gets padded to 13
        price = PriceFactory(product_code="123456789100")
        self.assertEqual(price.product_code, "0123456789100")
        # barcode of length 13 with leading zero stays the same
        price = PriceFactory(product_code="0123456789100")
        self.assertEqual(price.product_code, "0123456789100")
        # barcode of length 13 without leading 0 stays the same
        price = PriceFactory(product_code="8658585456785")
        self.assertEqual(price.product_code, "8658585456785")
        # barcode of length 14 with leading zero gets trimmed to 13
        price = PriceFactory(product_code="00123456789100")
        self.assertEqual(price.product_code, "0123456789100")
        # barcode of length > 13 without leading 0 stays the same
        price = PriceFactory(product_code="8658585456785867")
        self.assertEqual(price.product_code, "8658585456785867")
        # barcode with letters stays the same
        price = PriceFactory(product_code="12345678910A")
        self.assertEqual(price.product_code, "12345678910A")
        price = PriceFactory(product_code="0012345678910A")
        self.assertEqual(price.product_code, "0012345678910A")

    def test_price_without_product_validation(self):
        # product_code should not be set
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            category_tag="en:tomatoes",
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            labels_tags=["en:organic"],
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            origins_tags=["en:france"],
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            price_per=price_constants.PRICE_PER_UNIT,
        )
        # product_code not set: ok
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        # both product_code & category_tag not set
        self.assertRaises(
            ValidationError, PriceFactory, product_code="", category_tag=""
        )

    def test_price_category_tag_validation(self):
        for TUPLE_OK in [
            ("en: Tomatoes", "en:tomatoes"),
            ("fr: Pommes", "en:apples"),
            ("fr: Soupe aux lentilles", "en:lentil-soups"),
            ("fr: Grenoble", "fr:grenoble"),  # valid (even if not in the taxonomy)
        ]:
            price = PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag=TUPLE_OK[0],
                price=3,
                price_per=price_constants.PRICE_PER_KILOGRAM,
            )
            self.assertEqual(price.category_tag, TUPLE_OK[1])
        with self.assertRaises(ValidationError) as cm:
            PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="test",
                price=3,
                price_per=price_constants.PRICE_PER_KILOGRAM,
            )
        self.assertEqual(
            cm.exception.messages[0],
            "Invalid value: 'test', expected value to be in 'lang:tag' format",
        )

    def test_price_labels_tags_validation(self):
        # TYPE_PRODUCT
        for TUPLE_OK in [(None, None), ("", None), ([], None)]:
            with self.subTest(TUPLE_OK=TUPLE_OK):
                price = PriceFactory(
                    type=price_constants.TYPE_PRODUCT,
                    product_code="8001505005707",
                    labels_tags=TUPLE_OK[0],
                    price=5,
                )
                self.assertEqual(price.labels_tags, TUPLE_OK[1])
        # TYPE_CATEGORY
        for TUPLE_OK in [
            (None, []),
            ("", []),
            (["en:organic"], ["en:organic"]),
            (
                [
                    "fr: Nutriscore A",
                    "fr: Bio",
                    "es: Comercio justo y orgánico",
                    "en: Tag To be Created",
                ],
                [
                    "en:nutriscore-grade-a",
                    "en:organic",
                    "en:fair-trade-organic",
                    "en:tag-to-be-created",
                ],
            ),
        ]:
            with self.subTest(TUPLE_OK=TUPLE_OK):
                price = PriceFactory(
                    type=price_constants.TYPE_CATEGORY,
                    category_tag="en:tomatoes",
                    labels_tags=TUPLE_OK[0],
                    price=3,
                    price_per=price_constants.PRICE_PER_KILOGRAM,
                )
                self.assertEqual(price.labels_tags, TUPLE_OK[1])
        for TUPLE_NOT_OK in [
            ("en:organic", json.JSONDecodeError),
            (5, TypeError),
            ([""], ValidationError),
            (["en:organic", "test"], ValidationError),
        ]:
            with self.subTest(TUPLE_NOT_OK=TUPLE_NOT_OK):
                self.assertRaises(
                    TUPLE_NOT_OK[1],
                    PriceFactory,
                    type=price_constants.TYPE_CATEGORY,
                    category_tag="en:tomatoes",
                    labels_tags=TUPLE_NOT_OK[0],
                    price=3,
                    price_per=price_constants.PRICE_PER_KILOGRAM,
                )

    def test_price_origins_tags_validation(self):
        # TYPE_PRODUCT
        for TUPLE_OK in [(None, None), ("", None), ([], None)]:
            with self.subTest(TUPLE_OK=TUPLE_OK):
                price = PriceFactory(
                    type=price_constants.TYPE_PRODUCT,
                    product_code="8001505005707",
                    origins_tags=TUPLE_OK[0],
                    price=5,
                )
                self.assertEqual(price.origins_tags, TUPLE_OK[1])
        # TYPE_CATEGORY
        for TUPLE_OK in [
            (None, []),
            ("", []),
            (["en:france"], ["en:france"]),
            (["en:France"], ["en:france"]),
            (["fr:Allemagne"], ["en:germany"]),
            (["de:Deutschland", "es: España"], ["en:germany", "en:spain"]),
            (["fr: Fairyland"], ["fr:fairyland"]),
        ]:
            with self.subTest(TUPLE_OK=TUPLE_OK):
                price = PriceFactory(
                    type=price_constants.TYPE_CATEGORY,
                    category_tag="en:tomatoes",
                    origins_tags=TUPLE_OK[0],
                    price=3,
                    price_per=price_constants.PRICE_PER_KILOGRAM,
                )
                self.assertEqual(price.origins_tags, TUPLE_OK[1])
        for TUPLE_NOT_OK in [
            ("en:france", json.JSONDecodeError),
            (5, TypeError),
            ([""], ValidationError),
            (["en:france", "test"], ValidationError),
        ]:
            with self.subTest(TUPLE_NOT_OK=TUPLE_NOT_OK):
                self.assertRaises(
                    TUPLE_NOT_OK[1],
                    PriceFactory,
                    type=price_constants.TYPE_CATEGORY,
                    category_tag="en:tomatoes",
                    origins_tags=TUPLE_NOT_OK[0],
                    price=3,
                    price_per=price_constants.PRICE_PER_KILOGRAM,
                )

    def test_price_price_validation(self):
        for PRICE_OK in [
            0,
            5,
            Decimal("1.5"),
            Decimal("1.55"),
            Decimal("1.555"),  # max 3 decimals
            1234567,  # max 7 numbers (and 3 decimals)
            Decimal("1234567.890"),  # max 10 digits (7 numbers and 3 decimals)
        ]:
            with self.subTest(PRICE_OK=PRICE_OK):
                PriceFactory(price=PRICE_OK)
        for PRICE_NOT_OK in [
            -5,
            "test",
            None,
            "None",
            Decimal("1.5555"),
            12345678,
            Decimal("12345678.90"),
            # True
        ]:
            with self.subTest(PRICE_NOT_OK=PRICE_NOT_OK):
                self.assertRaises(ValidationError, PriceFactory, price=PRICE_NOT_OK)
        # price_per
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            price=3,
            price_per=None,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            price=3,
            price_per="test",
        )

    def test_price_discount_validation(self):
        # price set, price_without_discount null
        PriceFactory(price=3, price_is_discounted=False, price_without_discount=None)
        PriceFactory(price=3, price_is_discounted=True, price_without_discount=None)
        # price null, price_without_discount set
        for PRICE_WITHOUT_DISCOUNT_OK in [5, 0, None]:
            PriceFactory(
                price=0,
                price_is_discounted=True,
                price_without_discount=PRICE_WITHOUT_DISCOUNT_OK,
            )
        for PRICE_WITHOUT_DISCOUNT_NOT_OK in [-5, "test", "None"]:
            self.assertRaises(
                ValidationError,
                PriceFactory,
                price=None,
                price_is_discounted=True,
                price_without_discount=PRICE_WITHOUT_DISCOUNT_NOT_OK,
            )
        # both price & price_without_discount set
        PriceFactory(price=3, price_is_discounted=True, price_without_discount=5)
        self.assertRaises(
            ValidationError,
            PriceFactory,
            price=10,
            price_is_discounted=True,
            price_without_discount=5,
        )
        # discount_type
        price_not_discounted = PriceFactory(price=3)
        self.assertEqual(price_not_discounted.price_is_discounted, False)
        self.assertEqual(price_not_discounted.discount_type, None)
        price_discounted_1 = PriceFactory(
            price=3,
            price_is_discounted=True,
            discount_type=price_constants.DISCOUNT_TYPE_QUANTITY,
        )
        self.assertEqual(
            price_discounted_1.discount_type, price_constants.DISCOUNT_TYPE_QUANTITY
        )
        price_discounted_2 = PriceFactory(
            price=3, price_is_discounted=True, discount_type=None
        )
        self.assertEqual(price_discounted_2.discount_type, None)
        self.assertRaises(
            ValidationError,
            PriceFactory,
            price=10,
            discount_type=price_constants.DISCOUNT_TYPE_QUANTITY,
        )

    def test_price_currency_validation(self):
        for CURRENCY_OK in ["EUR", "USD"]:
            PriceFactory(currency=CURRENCY_OK)
        for CURRENCY_NOT_OK in ["test", "None"]:
            self.assertRaises(ValidationError, PriceFactory, currency=CURRENCY_NOT_OK)

    def test_price_date_validation(self):
        for DATE_OK in [None, "2024-01-01"]:
            PriceFactory(date=DATE_OK)
        for DATE_NOT_OK in ["3000-01-01", "01-01-2000"]:
            self.assertRaises(ValidationError, PriceFactory, date=DATE_NOT_OK)

    def test_price_location_validation(self):
        location_osm = LocationFactory()
        location_online = LocationFactory(type=location_constants.TYPE_ONLINE)
        # both location_osm_id & location_osm_type not set
        PriceFactory(location_osm_id=None, location_osm_type=None)
        # location_osm_id
        for LOCATION_OSM_ID_OK in location_constants.OSM_ID_OK_LIST:
            PriceFactory(
                location_osm_id=LOCATION_OSM_ID_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in location_constants.OSM_ID_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                PriceFactory,
                location_osm_id=LOCATION_OSM_ID_NOT_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        # location_osm_type
        for LOCATION_OSM_TYPE_OK in location_constants.OSM_TYPE_OK_LIST:
            PriceFactory(
                location_osm_id=652825274, location_osm_type=LOCATION_OSM_TYPE_OK
            )
        for LOCATION_OSM_TYPE_NOT_OK in location_constants.OSM_TYPE_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                PriceFactory,
                location_osm_id=652825274,
                location_osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )
        # location_id unknown
        self.assertRaises(
            ValidationError,
            PriceFactory,
            location_id=999,
            location_osm_id=None,
            location_osm_type=None,
        )
        # cannot mix location_id & location_osm_id/type
        self.assertRaises(
            ValidationError,
            PriceFactory,
            location_id=location_osm.id,
            location_osm_id=None,  # needed
            location_osm_type=None,  # needed
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            location_id=location_online.id,
            location_osm_id=LOCATION_OSM_ID_OK,  # should be None
        )
        # location_id ok
        PriceFactory(
            location_id=location_osm.id,
            location_osm_id=location_osm.osm_id,
            location_osm_type=location_osm.osm_type,
        )
        PriceFactory(
            location_id=location_online.id, location_osm_id=None, location_osm_type=None
        )

    def test_price_proof_validation(self):
        user_session = SessionFactory()
        user_proof_receipt = ProofFactory(
            type=proof_constants.TYPE_RECEIPT,
            location_osm_id=652825274,
            location_osm_type=location_constants.OSM_TYPE_NODE,
            date="2024-06-30",
            currency="EUR",
            owner=user_session.user.user_id,
        )
        proof_gdpr = ProofFactory(
            type=proof_constants.TYPE_GDPR_REQUEST,
            location_osm_id=169450062,
            location_osm_type=location_constants.OSM_TYPE_NODE,
            date="2024-10-01",
            currency="EUR",
        )
        proof_price_tag = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        # proof not set
        PriceFactory(proof_id=None, owner=user_proof_receipt.owner)
        # proof unknown
        self.assertRaises(
            ValidationError, PriceFactory, proof_id=999, owner=user_proof_receipt.owner
        )
        # same price & proof fields
        PriceFactory(
            proof_id=user_proof_receipt.id,
            location_osm_id=user_proof_receipt.location_osm_id,
            location_osm_type=user_proof_receipt.location_osm_type,
            date=user_proof_receipt.date,
            currency=user_proof_receipt.currency,
            owner=user_proof_receipt.owner,
        )
        # difference price and proof owner: raise a ValidationError
        # if the proof type is different than PRICE_TAG
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof_id=proof_gdpr.id,  # gdpr proof
            location_osm_id=proof_gdpr.location_osm_id,
            location_osm_type=proof_gdpr.location_osm_type,
            date=proof_gdpr.date,
            currency=proof_gdpr.currency,
            owner=user_proof_receipt.owner,  # different owner
        )
        # different price & proof owner: ok for PRICE_TAG proofs
        PriceFactory(
            proof_id=proof_price_tag.id,
            location_osm_id=user_proof_receipt.location_osm_id,
            location_osm_type=user_proof_receipt.location_osm_type,
            date=user_proof_receipt.date,
            currency=user_proof_receipt.currency,
            owner=user_proof_receipt.owner,  # different owner
        )
        # proof location_osm_id & location_osm_type
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof_id=user_proof_receipt.id,
            location_osm_id=5,  # different location_osm_id
            location_osm_type=user_proof_receipt.location_osm_type,
            date=user_proof_receipt.date,
            currency=user_proof_receipt.currency,
            owner=user_proof_receipt.owner,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof_id=user_proof_receipt.id,
            location_osm_id=user_proof_receipt.location_osm_id,
            location_osm_type="WAY",  # different location_osm_type
            date=user_proof_receipt.date,
            currency=user_proof_receipt.currency,
            owner=user_proof_receipt.owner,
        )
        # proof date & currency
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof_id=user_proof_receipt.id,
            location_osm_id=user_proof_receipt.location_osm_id,
            location_osm_type=user_proof_receipt.location_osm_type,
            date="2024-07-01",  # different date
            currency=user_proof_receipt.currency,
            owner=user_proof_receipt.owner,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof_id=user_proof_receipt.id,
            location_osm_id=user_proof_receipt.location_osm_id,
            location_osm_type=user_proof_receipt.location_osm_type,
            date=user_proof_receipt.date,
            currency="USD",  # different currency
            owner=user_proof_receipt.owner,
        )
        # receipt_quantity
        for RECEIPT_QUANTITY_NOT_OK in [-5, "test", Decimal("0.9999")]:
            with self.subTest(RECEIPT_QUANTITY_NOT_OK=RECEIPT_QUANTITY_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    PriceFactory,
                    proof_id=user_proof_receipt.id,
                    location_osm_id=user_proof_receipt.location_osm_id,
                    location_osm_type=user_proof_receipt.location_osm_type,
                    date=user_proof_receipt.date,
                    currency=user_proof_receipt.currency,
                    owner=user_proof_receipt.owner,
                    receipt_quantity=RECEIPT_QUANTITY_NOT_OK,
                )
        for RECEIPT_QUANTITY_OK in [None, 0, 1, 2, Decimal("1.5"), Decimal("0.395")]:
            with self.subTest(RECEIPT_QUANTITY_OK=RECEIPT_QUANTITY_OK):
                PriceFactory(
                    proof_id=user_proof_receipt.id,
                    location_osm_id=user_proof_receipt.location_osm_id,
                    location_osm_type=user_proof_receipt.location_osm_type,
                    date=user_proof_receipt.date,
                    currency=user_proof_receipt.currency,
                    owner=user_proof_receipt.owner,
                    receipt_quantity=RECEIPT_QUANTITY_OK,
                )

    def test_price_count_increment(self):
        user_session = SessionFactory()
        user_proof_1 = ProofFactory(owner=user_session.user.user_id)
        user_proof_2 = ProofFactory(owner=user_session.user.user_id)
        location = LocationFactory()
        product = ProductFactory()
        PriceFactory(
            proof_id=user_proof_1.id,
            location_osm_id=location.osm_id,
            location_osm_type=location.osm_type,
            product_code=product.code,
            owner=user_session.user.user_id,
        )
        self.assertEqual(
            User.objects.get(user_id=user_session.user.user_id).price_count, 1
        )
        self.assertEqual(Proof.objects.get(id=user_proof_1.id).price_count, 1)
        self.assertEqual(Location.objects.get(id=location.id).price_count, 1)
        self.assertEqual(Product.objects.get(id=product.id).price_count, 1)
        PriceFactory(
            proof_id=user_proof_2.id,
            location_osm_id=location.osm_id,
            location_osm_type=location.osm_type,
            product_code=product.code,
            owner=user_session.user.user_id,
        )
        self.assertEqual(
            User.objects.get(user_id=user_session.user.user_id).price_count, 2
        )
        self.assertEqual(Proof.objects.get(id=user_proof_2.id).price_count, 1)
        self.assertEqual(Location.objects.get(id=location.id).price_count, 2)
        self.assertEqual(Product.objects.get(id=product.id).price_count, 2)

    def test_price_set_is_duplicate_of_product_type(self):
        user_session_1 = SessionFactory()
        user_session_2 = SessionFactory()
        proof_1 = ProofFactory(owner=user_session_1.user.user_id)
        proof_2 = ProofFactory(owner=user_session_2.user.user_id)
        location_1 = LocationFactory()
        location_2 = LocationFactory(
            osm_id=location_1.osm_id + 1, osm_type=location_1.osm_type
        )
        product = ProductFactory()

        ref_price_kwargs = {
            "type": "PRODUCT",
            "proof_id": proof_1.id,
            "location_osm_id": location_1.osm_id,
            "location_osm_type": location_1.osm_type,
            "product_code": product.code,
            "category_tag": None,
            "owner": user_session_1.user.user_id,
            "date": "2025-01-01",
            "currency": "EUR",
            "price": Decimal("1.99"),
            "price_is_discounted": False,
            "price_without_discount": None,
            "discount_type": None,
            "labels_tags": None,
            "origins_tags": None,
        }
        new_price_kwargs = ref_price_kwargs | {
            "proof_id": proof_2.id,
            "owner": user_session_2.user.user_id,
        }
        ref_price_1 = PriceFactory(**ref_price_kwargs)
        for new_price, is_duplicate in (
            (
                PriceFactory(**new_price_kwargs),
                True,
            ),
            (
                # Different location
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "location_osm_id": location_2.osm_id,
                            "location_osm_type": location_2.osm_type,
                        }
                    )
                ),
                False,
            ),
            (
                # Different price
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "price": Decimal("2.90"),
                        }
                    )
                ),
                False,
            ),
            (
                # Different price without discount
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "price_is_discounted": True,
                            "price_without_discount": Decimal("3.0"),
                        }
                    )
                ),
                False,
            ),
            (
                # Different date
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "date": "2024-01-01",
                        }
                    )
                ),
                False,
            ),
            (
                # Different product code
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "product_code": "3259685685824",
                        }
                    )
                ),
                False,
            ),
        ):
            self.assertEqual(
                new_price.duplicate_of_id, ref_price_1.id if is_duplicate else None
            )
            # Delete the price so that we only compare to ref
            new_price.delete()

    def test_price_set_is_duplicate_of_category_type(self):
        user_session_1 = SessionFactory()
        user_session_2 = SessionFactory()
        proof_1 = ProofFactory(owner=user_session_1.user.user_id)
        proof_2 = ProofFactory(owner=user_session_2.user.user_id)
        location_1 = LocationFactory()
        location_2 = LocationFactory(
            osm_id=location_1.osm_id + 1, osm_type=location_1.osm_type
        )
        ref_price_kwargs = {
            "type": "CATEGORY",
            "price_per": price_constants.PRICE_PER_KILOGRAM,
            "proof_id": proof_1.id,
            "location_osm_id": location_1.osm_id,
            "location_osm_type": location_1.osm_type,
            "product_code": None,
            "category_tag": "en:pumpkins",
            "owner": user_session_1.user.user_id,
            "date": "2025-01-01",
            "currency": "EUR",
            "price": Decimal("1.99"),
            "price_is_discounted": False,
            "price_without_discount": None,
            "discount_type": None,
            "labels_tags": None,
            "origins_tags": None,
        }
        new_price_kwargs = ref_price_kwargs | {
            "proof_id": proof_2.id,
            "owner": user_session_2.user.user_id,
        }
        ref_price_1 = PriceFactory(**ref_price_kwargs)
        for new_price, is_duplicate in (
            (
                PriceFactory(**new_price_kwargs),
                True,
            ),
            (
                # Different location
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "location_osm_id": location_2.osm_id,
                            "location_osm_type": location_2.osm_type,
                        }
                    )
                ),
                False,
            ),
            (
                # Different price
                PriceFactory(**(new_price_kwargs | {"price": Decimal("2.99")})),
                False,
            ),
            (
                # Different price without discount
                PriceFactory(
                    **(
                        new_price_kwargs
                        | {
                            "price_is_discounted": True,
                            "price_without_discount": Decimal("3.00"),
                        }
                    )
                ),
                False,
            ),
            (
                # Different date
                PriceFactory(**(new_price_kwargs | {"date": "2024-01-01"})),
                False,
            ),
            (
                # Different category tag
                PriceFactory(**(new_price_kwargs | {"category_tag": "en:apples"})),
                False,
            ),
            (
                # Different price_per
                PriceFactory(
                    **(new_price_kwargs | {"price_per": price_constants.PRICE_PER_UNIT})
                ),
                False,
            ),
        ):
            self.assertEqual(
                new_price.duplicate_of_id, ref_price_1.id if is_duplicate else None
            )
            # Delete the price so that we only compare to ref
            new_price.delete()


class PriceModelUpdateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_session = SessionFactory()
        user_proof = ProofFactory(owner=user_session.user.user_id)
        location = LocationFactory()
        cls.price = PriceFactory(
            product_code="8850187002197",
            price=10,
            proof_id=user_proof.id,
            location_osm_id=location.osm_id,
            location_osm_type=location.osm_type,
            owner=user_session.user.user_id,
        )

    def test_price_update(self):
        # before
        self.assertEqual(self.price.price, 10)
        # update price
        self.price.price = 5
        self.price.save()
        # after
        self.assertEqual(self.price.price, 5)

    def test_price_update_product_code(self):
        # before
        self.assertEqual(self.price.product_code, "8850187002197")
        product_8850187002197 = Product.objects.get(code=self.price.product_code)
        self.assertEqual(self.price.product, product_8850187002197)
        self.assertEqual(product_8850187002197.price_count, 1)
        self.assertFalse(Product.objects.filter(code="8001505005707").exists())
        # update product_code
        self.price.product_code = "8001505005707"
        self.price.save()
        # after
        self.assertEqual(self.price.product_code, "8001505005707")
        product_8850187002197.refresh_from_db()
        self.assertEqual(product_8850187002197.price_count, 1)  # TODO: should be 0
        product_8001505005707 = Product.objects.get(code="8001505005707")
        self.assertEqual(product_8001505005707.price_count, 0)  # TODO: should be 1
        self.assertEqual(self.price.product, product_8001505005707)


class PriceModelDeleteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.user_proof = ProofFactory(owner=cls.user_session.user.user_id)
        cls.location = LocationFactory()
        cls.product = ProductFactory()
        cls.price = PriceFactory(
            proof_id=cls.user_proof.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            product_code=cls.product.code,
            owner=cls.user_session.user.user_id,
        )

    def test_price_count_decrement(self):
        # before
        self.user_session.user.refresh_from_db()
        self.user_proof.refresh_from_db()
        self.location.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.user_session.user.price_count, 1)
        self.assertEqual(self.user_proof.price_count, 1)
        self.assertEqual(self.location.price_count, 1)
        self.assertEqual(self.product.price_count, 1)
        # delete price
        self.price.delete()
        # after
        self.user_session.user.refresh_from_db()
        self.user_proof.refresh_from_db()
        self.location.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.user_session.user.price_count, 0)
        self.assertEqual(self.user_proof.price_count, 0)
        self.assertEqual(self.location.price_count, 0)
        self.assertEqual(self.product.price_count, 0)


class PriceModelHistoryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.user_proof = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG, owner=cls.user_session.user.user_id
        )
        cls.location = LocationFactory()
        cls.product_8001505005707 = ProductFactory(**PRODUCT_8001505005707)
        cls.product_8850187002197 = ProductFactory(**PRODUCT_8850187002197)
        cls.price = PriceFactory(
            price=3,
            proof_id=cls.user_proof.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            product_code=cls.product_8001505005707.code,
            owner=cls.user_session.user.user_id,
        )

    def test_price_history(self):
        self.assertEqual(self.price.history.count(), 1)
        self.assertEqual(self.price.history.first().history_type, "+")
        self.assertEqual(self.price.history.first().history_user_id, None)
        # update the price (date & product)
        self.price.price = 5
        self.price.product_code = self.product_8850187002197.code
        self.price.save()
        self.assertEqual(self.price.history.count(), 2)
        self.assertEqual(self.price.history.first().history_type, "~")
        self.assertEqual(self.price.history.first().history_user_id, None)
        fields_changed_list = [
            change.field
            for change in self.price.history.first()
            .diff_against(self.price.history.first().prev_record)
            .changes
        ]
        self.assertEqual(fields_changed_list, ["price", "product", "product_code"])
        # bulk update the price
        self.price.price = 10
        bulk_update_with_history(
            [self.price], Price, ["price"], default_user="moderator-2"
        )
        self.assertEqual(self.price.history.count(), 3)
        self.assertEqual(self.price.history.first().history_type, "~")
        self.assertEqual(self.price.history.first().history_user_id, "moderator-2")
        fields_changed_list = [
            change.field
            for change in self.price.history.first()
            .diff_against(self.price.history.first().prev_record)
            .changes
        ]
        self.assertEqual(fields_changed_list, ["price"])
        # delete the price
        price_id = self.price.id
        self.price._history_user = "moderator-3"
        self.price.delete()
        self.assertEqual(Price.history.filter(id=price_id).count(), 4)
        self.assertEqual(Price.history.filter(id=price_id).first().history_type, "-")
        self.assertEqual(
            Price.history.filter(id=price_id).first().history_user_id, "moderator-3"
        )

    def test_price_get_history_list(self):
        history_list = self.price.get_history_list()
        self.assertEqual(len(history_list), 1)
        self.assertEqual(history_list[0]["history_type"], "+")
        self.assertEqual(len(history_list[0]["changes"]), 0)
        # update the price
        self.price.price = 5
        self.price.save()
        history_list = self.price.get_history_list()
        self.assertEqual(len(history_list), 2)
        self.assertEqual(history_list[0]["history_type"], "~")
        self.assertEqual(len(history_list[0]["changes"]), 1)
        self.assertEqual(history_list[0]["changes"][0]["field"], "price")
        self.assertEqual(history_list[0]["changes"][0]["old"], Decimal("3"))
        self.assertEqual(history_list[0]["changes"][0]["new"], Decimal("5"))
        # save the price without changes
        self.price.save()
        history_list = self.price.get_history_list()
        self.assertEqual(len(history_list), 2)  # empty history entry ignored


class PriceCommandTest(TestCase):
    def test_normalize_barcodes_command(self):
        # bulk_create to skip save() & clean()
        Product.objects.bulk_create(
            [
                ProductFactory.build(code="123456789100"),  # not normalized
                ProductFactory.build(code="0123456789100"),  # normalized
            ]
        )
        self.assertEqual(Product.objects.count(), 2)
        Price.objects.bulk_create(
            [
                PriceFactory.build(
                    type=price_constants.TYPE_PRODUCT,
                    product_code="123456789100",
                    product_id=Product.objects.get(code="123456789100").id,
                ),
                PriceFactory.build(
                    type=price_constants.TYPE_PRODUCT,
                    product_code="0123456789100",
                    product_id=Product.objects.get(code="0123456789100").id,
                ),
            ]
        )
        self.assertEqual(Price.objects.count(), 2)
        call_command("normalize_barcodes", "--apply")
        # products have been merged
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().code, "0123456789100")
        self.assertEqual(Price.objects.count(), 2)
        # prices now have normalized product_code & share the same product_id
        for price in Price.objects.all():
            self.assertEqual(price.product_code, "0123456789100")
            self.assertEqual(price.product_id, Product.objects.first().id)
