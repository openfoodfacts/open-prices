from sqlalchemy.orm import Session

from app import crud
from app.schemas import LocationCreate, PriceBase, ProductCreate


def create_price_product(db: Session, price: PriceBase):
    if price.product_code:
        # get or create the corresponding product
        product = ProductCreate(code=price.product_code)
        db_product = crud.get_or_create_product(db, product=product)
        # link the product to the price
        crud.set_price_product(db, price=price, product=db_product)


def create_price_location(db: Session, price: PriceBase):
    if price.location_osm_id and price.location_osm_type:
        # get or create the corresponding location
        location = LocationCreate(
            osm_id=price.location_osm_id, osm_type=price.location_osm_type
        )
        db_location = crud.get_or_create_location(db, location=location)
        # link the location to the price
        crud.set_price_location(db, price=price, location=db_location)
