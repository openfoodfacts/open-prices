from sqlalchemy.orm import Session

from app import crud
from app.schemas import LocationCreate, PriceBase


def create_price_location(db: Session, price: PriceBase):
    if price.location_osm_id and price.location_osm_type:
        # check if an existing location exists
        location = LocationCreate(
            osm_id=price.location_osm_id, osm_type=price.location_osm_type
        )
        db_location = crud.get_location_by_osm_id_and_type(
            db, osm_id=location.osm_id, osm_type=location.osm_type
        )
        if db_location:
            print("existing", db_location)
            pass
        else:
            db_location = crud.create_location(db, location=location)
            print("create", db_location)
