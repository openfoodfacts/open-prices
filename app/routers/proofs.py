from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.auth import get_current_user
from app.db import get_db
from app.enums import CurrencyEnum, LocationOSMEnum, ProofTypeEnum
from app.models import Proof

router = APIRouter(prefix="/proofs")


@router.get("", response_model=Page[schemas.ProofFullWithRelations])
def get_user_proofs(
    current_user: schemas.UserCreate = Depends(get_current_user),
    filters: schemas.ProofFilter = FilterDepends(schemas.ProofFilter),
    db: Session = Depends(get_db),
) -> Select[tuple[Proof]]:
    """
    Get all the proofs uploaded by the current user.

    This endpoint requires authentication.
    """
    filters.owner = current_user.user_id
    return paginate(db, crud.get_proofs_query(filters=filters))


@router.post(
    "/upload",
    response_model=schemas.ProofFull,
    status_code=status.HTTP_201_CREATED,
)
def upload_proof(
    file: UploadFile,
    type: Annotated[ProofTypeEnum, Form(description="The type of the proof")],
    background_tasks: BackgroundTasks,
    location_osm_id: Optional[str] = Form(
        description="Proof location OSM id", default=None
    ),
    location_osm_type: Optional[LocationOSMEnum] = Form(
        description="Proof location OSM type", default=None
    ),
    date: Optional[str] = Form(description="Proof date", default=None),
    currency: Optional[CurrencyEnum] = Form(description="Proof currency", default=None),
    app_name: str | None = None,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Proof:
    """
    Upload a proof file.

    The POST request must be a multipart/form-data request with a file field
    named "file".

    This endpoint requires authentication.
    """
    file_path, mimetype = crud.create_proof_file(file)
    # create proof
    db_proof = crud.create_proof(
        db,
        file_path,
        mimetype,
        type=type,
        user=current_user,
        location_osm_id=location_osm_id,
        location_osm_type=location_osm_type,
        date=date,
        currency=currency,
        source=app_name,
    )
    # relationships
    background_tasks.add_task(tasks.create_proof_location, db, proof=db_proof)
    return db_proof


@router.get(
    "/{proof_id}",
    response_model=schemas.ProofFull,
)
def get_user_proof_by_id(
    proof_id: int,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Proof:
    # fetch proof with id = proof_id
    db_proof = crud.get_proof_by_id(db, id=proof_id)

    if not db_proof:
        raise HTTPException(
            status_code=404,
            detail=f"Proof with id {proof_id} not found",
        )
    # Check if the proof belongs to the current user,
    # if it doesn't, the user needs to be a moderator
    if db_proof.owner != current_user.user_id and not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Proof does not belong to current user",
        )

    return db_proof


@router.patch(
    path="/{proof_id}",
    response_model=schemas.ProofFull,
    status_code=status.HTTP_200_OK,
)
def update_proof(
    proof_id: int,
    proof_new_values: schemas.ProofBasicUpdatableFields,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Proof:
    """
    Update a proof.

    This endpoint requires authentication.
    A user can update only owned proofs.
    """
    # fetch proof with id = proof_id
    db_proof = crud.get_proof_by_id(db, id=proof_id)

    if not db_proof:
        raise HTTPException(
            status_code=404,
            detail=f"Proof with id {proof_id} not found",
        )
    # Check if the proof belongs to the current user,
    # if it doesn't, the user needs to be a moderator
    if db_proof.owner != current_user.user_id and not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Proof does not belong to current user",
        )

    # updated proof
    return crud.update_proof(db, db_proof, proof_new_values)


@router.delete(
    "/{proof_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_proof(
    proof_id: int,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a proof.

    This endpoint requires authentication.
    A user can delete only owned proofs.
    Can delete only proofs that are not associated with prices.
    A moderator can delete not owned proofs.
    """
    # fetch proof with id = proof_id
    db_proof = crud.get_proof_by_id(db, id=proof_id)

    if not db_proof:
        raise HTTPException(
            status_code=404,
            detail=f"Proof with code {proof_id} not found",
        )
    # Check if the proof belongs to the current user,
    # if it doesn't, the user needs to be a moderator
    if db_proof.owner != current_user.user_id and not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Proof does not belong to current user",
        )
    # check if the proof is associated with some prices
    if len(db_proof.prices) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Proof has prices associated with it",
        )

    # delete proof
    crud.delete_proof(db, db_proof)
    return None
