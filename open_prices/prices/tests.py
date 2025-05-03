from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

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

    def test_has_tags(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_tag("challenge-1").count(), 1)
        self.assertEqual(Price.objects.has_tag("unknown").count(), 0)


class PriceChallengeQuerySetAndPropertyAndSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True,
            start_date="2024-12-30",
            end_date="2025-01-30",
            categories=["en:breakfasts"],
        )
        cls.product_8001505005707 = ProductFactory(
            **PRODUCT_8001505005707
        )  # in challenge
        cls.product_8850187002197 = ProductFactory(**PRODUCT_8850187002197)
        with freeze_time("2025-01-01"):  # during the challenge
            cls.price_11 = PriceFactory()
            cls.price_12 = PriceFactory(
                product_code="8001505005707", product=cls.product_8001505005707
            )
            cls.price_13 = PriceFactory(
                product_code="8850187002197", product=cls.product_8850187002197
            )

        with freeze_time("2025-01-30 22:00:00"):  # last day of the challenge
            cls.price_21 = PriceFactory()
            cls.price_22 = PriceFactory(
                product_code="8001505005707", product=cls.product_8001505005707
            )
            cls.price_23 = PriceFactory(
                product_code="8850187002197", product=cls.product_8850187002197
            )

        with freeze_time("2025-02-01"):  # after the challenge
            cls.price_31 = PriceFactory()
            cls.price_32 = PriceFactory(
                product_code="8001505005707", product=cls.product_8001505005707
            )
            cls.price_33 = PriceFactory(
                product_code="8850187002197", product=cls.product_8850187002197
            )

    def test_in_challenge_queryset(self):
        self.assertEqual(Price.objects.count(), 9)
        self.assertEqual(
            Price.objects.in_challenge(self.challenge_ongoing).count(), 1 + 1
        )

    def test_in_challenge_property(self):
        for price in Price.objects.all():
            if price in [self.price_12, self.price_22]:
                self.assertEqual(price.in_challenge(self.challenge_ongoing), True)
            else:
                self.assertEqual(price.in_challenge(self.challenge_ongoing), False)

    def test_on_create_signal(self):
        for price in Price.objects.all():  # refresh_from_db
            if price in [self.price_12, self.price_22]:
                self.assertIn(f"challenge-{self.challenge_ongoing.id}", price.tags)
            else:
                self.assertNotIn(f"challenge-{self.challenge_ongoing.id}", price.tags)


class PriceModelSaveTest(TestCase):
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

    def test_price_without_product_validation(self):
        # product_code set
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
        # product_code not set
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
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
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="fr: Grenoble",  # valid (even if not in the taxonomy)
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            labels_tags="en:organic",  # should be a list
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            labels_tags=[
                "en:organic",
                "test",
            ],  # not valid, no lang prefix before 'test'
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags=["en:france"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags="en:france",  # should be a list
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags=["en:france", "test"],  # not valid
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        # both product_code & category_tag not set
        self.assertRaises(
            ValidationError, PriceFactory, product_code="", category_tag=""
        )

    def test_price_category_validation(self):
        for input_category, expected_category in [
            ("en: Tomatoes", "en:tomatoes"),
            ("fr: Pommes", "en:apples"),
            ("fr: Soupe aux lentilles", "en:lentil-soups"),
        ]:
            price = PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag=input_category,
                price=3,
                price_per=price_constants.PRICE_PER_KILOGRAM,
            )
            self.assertEqual(price.category_tag, expected_category)

    def test_price_origin_validation(self):
        for input_origin_tags, expected_origin_tags in [
            (["en:France"], ["en:france"]),
            (["fr:Allemagne"], ["en:germany"]),
            (["de:Deutschland", "es: España"], ["en:germany", "en:spain"]),
            (["fr: Fairyland"], ["fr:fairyland"]),
        ]:
            price = PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="en:tomatoes",
                origins_tags=input_origin_tags,
                price=3,
                price_per=price_constants.PRICE_PER_KILOGRAM,
            )
            self.assertEqual(price.origins_tags, expected_origin_tags)

    def test_price_price_validation(self):
        for PRICE_OK in [0, 5, Decimal("1.5")]:
            PriceFactory(price=PRICE_OK)
        for PRICE_NOT_OK in [-5, "test", None, "None"]:  # True
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


class PriceModelUpdateTest(TestCase):
    def test_price_update(self):
        user_session = SessionFactory()
        user_proof = ProofFactory(owner=user_session.user.user_id)
        location = LocationFactory()
        product = ProductFactory()
        price = PriceFactory(
            proof_id=user_proof.id,
            location_osm_id=location.osm_id,
            location_osm_type=location.osm_type,
            product_code=product.code,
            owner=user_session.user.user_id,
        )
        price.price = 5
        price.save()


class PriceModelDeleteTest(TestCase):
    def test_price_count_decrement(self):
        user_session = SessionFactory()
        user_proof = ProofFactory(owner=user_session.user.user_id)
        location = LocationFactory()
        product = ProductFactory()
        price = PriceFactory(
            proof_id=user_proof.id,
            location_osm_id=location.osm_id,
            location_osm_type=location.osm_type,
            product_code=product.code,
            owner=user_session.user.user_id,
        )
        self.assertEqual(
            User.objects.get(user_id=user_session.user.user_id).price_count, 1
        )
        self.assertEqual(Proof.objects.get(id=user_proof.id).price_count, 1)
        self.assertEqual(Location.objects.get(id=location.id).price_count, 1)
        self.assertEqual(Product.objects.get(id=product.id).price_count, 1)
        price.delete()
        self.assertEqual(
            User.objects.get(user_id=user_session.user.user_id).price_count, 0
        )
        self.assertEqual(Proof.objects.get(id=user_proof.id).price_count, 0)
        self.assertEqual(Location.objects.get(id=location.id).price_count, 0)
        self.assertEqual(Product.objects.get(id=product.id).price_count, 0)
