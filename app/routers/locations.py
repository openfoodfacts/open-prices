from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.db import get_db
from app.models import Location

router = APIRouter(prefix="/locations")


@router.get("", response_model=Page[schemas.LocationFull])
def get_locations(
    filters: schemas.LocationFilter = FilterDepends(schemas.LocationFilter),
    db: Session = Depends(get_db),
) -> list[Location]:
    return paginate(db, crud.get_locations_query(filters=filters))


@router.get(
    "/osm/{location_osm_type}/{location_osm_id}",
    response_model=schemas.LocationFull,
)
def get_location_by_osm(
    location_osm_type: str, location_osm_id: int, db: Session = Depends(get_db)
) -> Location:
    db_location = crud.get_location_by_osm_id_and_type(
        db, osm_id=location_osm_id, osm_type=location_osm_type.upper()
    )
    if not db_location:
        raise HTTPException(
            status_code=404,
            detail=f"Location with type {location_osm_type} & id {location_osm_id} not found",
        )
    return db_location


@router.get(
    "/{location_id}",
    response_model=schemas.LocationFull,
)
def get_location_by_id(location_id: int, db: Session = Depends(get_db)) -> Location:
    db_location = crud.get_location_by_id(db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {location_id} not found",
        )
    return db_location


@router.post(
    "",
    response_model=schemas.LocationFull,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    location: schemas.LocationCreate,
    response: Response,
    current_user: schemas.UserCreate = Depends(get_current_user),
    # app_name: str | None = None,
    db: Session = Depends(get_db),
) -> Location:
    """
    Create a new location.

    This endpoint requires authentication.
    """
    db_location, created = crud.get_or_create_location(
        db, location=location, if_create_then_fetch_osm_data=True
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return db_location
