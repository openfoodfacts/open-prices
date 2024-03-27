from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import get_db
from app.models import Product

router = APIRouter(prefix="/products")


@router.get("", response_model=Page[schemas.ProductFull])
def get_products(
    filters: schemas.ProductFilter = FilterDepends(schemas.ProductFilter),
    db: Session = Depends(get_db),
) -> list[Product]:
    return paginate(db, crud.get_products_query(filters=filters))


@router.get(
    "/code/{product_code}",
    response_model=schemas.ProductFull,
)
def get_product_by_code(product_code: str, db: Session = Depends(get_db)) -> Product:
    db_product = crud.get_product_by_code(db, code=product_code)
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with code {product_code} not found",
        )
    return db_product


@router.get(
    "/{product_id}",
    response_model=schemas.ProductFull,
)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)) -> Product:
    db_product = crud.get_product_by_id(db, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {product_id} not found",
        )
    return db_product
