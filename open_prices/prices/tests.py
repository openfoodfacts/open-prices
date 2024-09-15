from django.core.exceptions import ValidationError
from django.test import TestCase

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


class PriceQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PriceFactory(price=5, price_is_discounted=True, price_without_discount=10)
        PriceFactory(price=8)
        PriceFactory(price=10)

    def test_exclude_discounted(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.exclude_discounted().count(), 2)


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
            product_code=None,
            category_tag="en:tomatoes",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="test",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        PriceFactory(
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags="en:organic",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic", "test"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        PriceFactory(
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags=["en:france"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags="en:france",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags=["en:france", "test"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        # both product_code & category_tag not set
        self.assertRaises(
            ValidationError, PriceFactory, product_code="", category_tag=""
        )

    def test_price_price_validation(self):
        for PRICE_OK in [5, 0]:
            PriceFactory(price=PRICE_OK)
        for PRICE_NOT_OK in [-5, "test", None, "None"]:  # True
            self.assertRaises(ValidationError, PriceFactory, price=PRICE_NOT_OK)
        # price_per
        PriceFactory(
            product_code=None,
            category_tag="en:tomatoes",
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            price=3,
            price_per=None,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
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
        for PRICE_WITHOUT_DISCOUNT_NOT_OK in [-5, "test"]:
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

    def test_price_proof_validation(self):
        self.user_session = SessionFactory()
        self.user_proof = ProofFactory(
            type=proof_constants.TYPE_RECEIPT,
            location_osm_id=652825274,
            location_osm_type=location_constants.OSM_TYPE_NODE,
            date="2024-06-30",
            currency="EUR",
            owner=self.user_session.user.user_id,
        )
        self.proof_2 = ProofFactory()
        # proof not set
        PriceFactory(proof=None, owner=self.user_proof.owner)
        # same price & proof fields
        PriceFactory(
            proof=self.user_proof,
            location_osm_id=self.user_proof.location_osm_id,
            location_osm_type=self.user_proof.location_osm_type,
            date=self.user_proof.date,
            currency=self.user_proof.currency,
            owner=self.user_proof.owner,
        )
        # different price & proof owner
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof=self.proof_2,  # different
            location_osm_id=self.user_proof.location_osm_id,
            location_osm_type=self.user_proof.location_osm_type,
            date=self.user_proof.date,
            currency=self.user_proof.currency,
            owner=self.user_proof.owner,
        )
        # proof location_osm_id & location_osm_type
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof=self.user_proof,
            location_osm_id=5,  # different location_osm_id
            location_osm_type=self.user_proof.location_osm_type,
            date=self.user_proof.date,
            currency=self.user_proof.currency,
            owner=self.user_proof.owner,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof=self.user_proof,
            location_osm_id=self.user_proof.location_osm_id,
            location_osm_type="WAY",  # different location_osm_type
            date=self.user_proof.date,
            currency=self.user_proof.currency,
            owner=self.user_proof.owner,
        )
        # proof date & currency
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof=self.user_proof,
            location_osm_id=self.user_proof.location_osm_id,
            location_osm_type=self.user_proof.location_osm_type,
            date="2024-07-01",  # different date
            currency=self.user_proof.currency,
            owner=self.user_proof.owner,
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            proof=self.user_proof,
            location_osm_id=self.user_proof.location_osm_id,
            location_osm_type=self.user_proof.location_osm_type,
            date=self.user_proof.date,
            currency="USD",  # different currency
            owner=self.user_proof.owner,
        )

    def test_price_count_increment(self):
        user_session = SessionFactory()
        user_proof_1 = ProofFactory(owner=user_session.user.user_id)
        user_proof_2 = ProofFactory(owner=user_session.user.user_id)
        location = LocationFactory()
        product = ProductFactory()
        PriceFactory(
            proof=user_proof_1,
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
            proof=user_proof_2,
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


class PriceModelDeleteTest(TestCase):
    def test_price_count_decrement(self):
        user_session = SessionFactory()
        user_proof = ProofFactory(owner=user_session.user.user_id)
        location = LocationFactory()
        product = ProductFactory()
        price = PriceFactory(
            proof=user_proof,
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
