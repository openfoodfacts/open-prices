from sqlalchemy.orm import Session

from app import crud
from app.schemas import LocationCreate, PriceBase, ProductCreate
from app.utils import (
    fetch_location_openstreetmap_details,
    fetch_product_openfoodfacts_details,
)


def create_price_product(db: Session, price: PriceBase):
    # The price may not have a product code, if it's the price of a
    # barcode-less product
    if price.product_code:
        # get or create the corresponding product
        product = ProductCreate(code=price.product_code)
        db_product, created = crud.get_or_create_product(db, product=product)
        # link the product to the price
        crud.set_price_product(db, price=price, product=db_product)
        # fetch data from OpenFoodFacts if created
        if created:
            product_openfoodfacts_details = fetch_product_openfoodfacts_details(
                product=db_product
            )
            if product_openfoodfacts_details:
                crud.update_product(
                    db, product=db_product, update_dict=product_openfoodfacts_details
                )


def create_price_location(db: Session, price: PriceBase):
    if price.location_osm_id and price.location_osm_type:
        # get or create the corresponding location
        location = LocationCreate(
            osm_id=price.location_osm_id, osm_type=price.location_osm_type
        )
        db_location, created = crud.get_or_create_location(db, location=location)
        # link the location to the price
        crud.set_price_location(db, price=price, location=db_location)
        # fetch data from OpenStreetMap if created
        if created:
            location_openstreetmap_details = fetch_location_openstreetmap_details(
                location=db_location
            )
            if location_openstreetmap_details:
                crud.update_location(
                    db, location=db_location, update_dict=location_openstreetmap_details
                )
