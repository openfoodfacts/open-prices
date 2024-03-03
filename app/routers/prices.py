import functools

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.auth import get_current_user, get_current_user_optional
from app.db import get_db
from app.models import Price

router = APIRouter(prefix="/prices")


def price_transformer(
    prices: list[Price], current_user: schemas.UserCreate | None = None
) -> list[Price]:
    """Transformer function used to remove the file_path of private proofs.

    If current_user is None, the file_path is removed for all proofs that are
    not public. Otherwise, the file_path is removed for all proofs that are not
    public and do not belong to the current user and is not a moderator.

    :param prices: the list of prices to transform
    :param current_user: the current user, if authenticated
    :return: the transformed list of prices
    """
    user_id = current_user.user_id if current_user else None
    for price in prices:
        if (
            price.proof
            and price.proof.is_public is False
            and price.proof.owner != user_id
            and not current_user.is_moderator
        ):
            price.proof.file_path = None
    return prices


@router.get(
    "",
    response_model=Page[schemas.PriceFullWithRelations],
)
def get_prices(
    filters: schemas.PriceFilter = FilterDepends(schemas.PriceFilter),
    db: Session = Depends(get_db),
    current_user: schemas.UserCreate | None = Depends(get_current_user_optional),
):
    return paginate(
        db,
        crud.get_prices_query(filters=filters),
        transformer=functools.partial(price_transformer, current_user=current_user),
    )


@router.post(
    "",
    response_model=schemas.PriceFull,
    status_code=status.HTTP_201_CREATED,
)
def create_price(
    price: schemas.PriceCreateWithValidation,
    background_tasks: BackgroundTasks,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new price.

    This endpoint requires authentication.
    """
    # check if we have a proof_id provided
    if price.proof_id is not None:
        db_proof = crud.get_proof_by_id(db, id=price.proof_id)
        if db_proof is None:
            # No proof exists with this id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proof not found",
            )
        else:
            # Check if the proof belongs to the current user,
            # or if the user is a moderator
            # Only proof uploaded by the user can be used
            if db_proof.owner != current_user.user_id and not current_user.is_moderator:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Proof does not belong to current user",
                )
    # create price
    db_price = crud.create_price(db, price=price, user=current_user)
    # update counts
    background_tasks.add_task(tasks.create_price_product, db, price=db_price)
    background_tasks.add_task(tasks.create_price_location, db, price=db_price)
    background_tasks.add_task(tasks.increment_user_price_count, db, user=current_user)
    if price.proof_id and db_proof:
        background_tasks.add_task(tasks.increment_proof_price_count, db, proof=db_proof)
    return db_price


@router.patch(
    path="/{price_id}",
    response_model=schemas.PriceFull,
    status_code=status.HTTP_200_OK,
)
def update_price(
    price_id: int,
    price_new_values: schemas.PriceBasicUpdatableFields,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a price.

    This endpoint requires authentication.
    A user can update only owned prices.
    """
    # fetch price with id = price_id
    db_price = crud.get_price_by_id(db, id=price_id)

    if not db_price:
        raise HTTPException(
            status_code=404,
            detail=f"Price with code {price_id} not found",
        )
    # Check if the price belongs to the current user
    if db_price.owner != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Price does not belong to current user",
        )

    # updated price
    return crud.update_price(db, db_price, price_new_values)


@router.delete(
    "/{price_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_price(
    price_id: int,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a price.

    This endpoint requires authentication.
    A user can delete only owned prices.
    """
    db_price = crud.get_price_by_id(db, id=price_id)
    # get price
    if not db_price:
        raise HTTPException(
            status_code=404,
            detail=f"Price with code {price_id} not found",
        )
    # Check if the price belongs to the current user
    if db_price.owner != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Price does not belong to current user",
        )
    # delete price
    crud.delete_price(db, db_price=db_price)
    return
