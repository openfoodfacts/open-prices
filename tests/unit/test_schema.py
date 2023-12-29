import datetime

import pydantic
import pytest

from app.schemas import CurrencyEnum, LocationOSMEnum, PriceCreate


class TestPriceCreate:
    def test_simple_price_with_barcode(self):
        price = PriceCreate(
            product_code="5414661000456",
            location_osm_id=123,
            location_osm_type=LocationOSMEnum.NODE,
            price=1.99,
            currency="EUR",
            date="2021-01-01",
        )
        assert price.product_code == "5414661000456"
        assert price.location_osm_id == 123
        assert price.location_osm_type == LocationOSMEnum.NODE
        assert price.price == 1.99
        assert price.currency == CurrencyEnum.EUR
        assert price.date == datetime.date.fromisoformat("2021-01-01")

    def test_simple_price_with_category(self):
        price = PriceCreate(
            category_tag="en:Fresh-apricots",
            labels_tags=["en:Organic", "fr:AB-agriculture-biologique"],
            origins_tags=["en:California", "en:Sweden"],
            location_osm_id=123,
            location_osm_type=LocationOSMEnum.NODE,
            price=1.99,
            currency="EUR",
            date="2021-01-01",
        )
        assert price.category_tag == "en:fresh-apricots"
        assert price.labels_tags == ["en:organic", "fr:ab-agriculture-biologique"]
        assert price.origins_tags == ["en:california", "en:sweden"]

    def test_simple_price_with_invalid_taxonomized_values(self):
        with pytest.raises(pydantic.ValidationError, match="Invalid category tag"):
            PriceCreate(
                category_tag="en:unknown-category",
                location_osm_id=123,
                location_osm_type=LocationOSMEnum.NODE,
                price=1.99,
                currency="EUR",
                date="2021-01-01",
            )

        with pytest.raises(pydantic.ValidationError, match="Invalid label tag"):
            PriceCreate(
                category_tag="en:carrots",
                labels_tags=["en:invalid"],
                location_osm_id=123,
                location_osm_type=LocationOSMEnum.NODE,
                price=1.99,
                currency="EUR",
                date="2021-01-01",
            )

        with pytest.raises(pydantic.ValidationError, match="Invalid origin tag"):
            PriceCreate(
                category_tag="en:carrots",
                origins_tags=["en:invalid"],
                location_osm_id=123,
                location_osm_type=LocationOSMEnum.NODE,
                price=1.99,
                currency="EUR",
                date="2021-01-01",
            )

    def test_simple_price_with_product_code_and_labels_tags_raise(self):
        with pytest.raises(
            pydantic.ValidationError,
            match="`labels_tags` can only be set for products without barcode",
        ):
            PriceCreate(
                product_code="5414661000456",
                labels_tags=["en:Organic", "fr:AB-agriculture-biologique"],
                location_osm_id=123,
                location_osm_type=LocationOSMEnum.NODE,
                price=1.99,
                currency="EUR",
                date="2021-01-01",
            )
