from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import get_db

router = APIRouter(prefix="/users")


@router.get("", response_model=Page[schemas.UserBase])
def get_users(
    db: Session = Depends(get_db),
    filters: schemas.UserFilter = FilterDepends(schemas.UserFilter),
):
    return paginate(db, crud.get_users_query(filters=filters))
