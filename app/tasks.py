from sqlalchemy.orm import Session

from app import crud
from app.schemas import LocationCreate, PriceBase


def create_price_location(db: Session, price: PriceBase):
    if price.location_osm_id and price.location_osm_type:
        # get or create the corresponding location
        location = LocationCreate(
            osm_id=price.location_osm_id, osm_type=price.location_osm_type
        )
        db_location = crud.get_or_create_location(db, location=location)
        # link the location to the price
        crud.set_price_location(db, price=price, location=db_location)
