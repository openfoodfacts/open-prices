from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.db import get_db
from app.enums import ProofTypeEnum
from app.models import Proof

router = APIRouter(prefix="/proofs")


@router.get("", response_model=Page[schemas.ProofFull])
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
    is_public: bool = Form(
        default=True,
        description="if true, the proof is public and is included in the API response. "
        "Set false only for RECEIPT proofs that contain personal information.",
    ),
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Proof:
    """
    Upload a proof file.

    The POST request must be a multipart/form-data request with a file field
    named "file".

    This endpoint requires authentication.
    """
    if not is_public and type is not ProofTypeEnum.RECEIPT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only receipts can be private",
        )
    file_path, mimetype = crud.create_proof_file(file)
    db_proof = crud.create_proof(
        db, file_path, mimetype, type=type, user=current_user, is_public=is_public
    )
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
    # get proof
    db_proof = crud.get_proof_by_id(db, id=proof_id)
    if not db_proof:
        raise HTTPException(
            status_code=404,
            detail=f"Proof with id {proof_id} not found",
        )
    # Check if the proof belongs to the current user,
    # if it doesn't, the user needs to be moderator
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
    # if it doesn't, the user needs to be moderator
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
    # get proof
    db_proof = crud.get_proof_by_id(db, id=proof_id)
    if not db_proof:
        raise HTTPException(
            status_code=404,
            detail=f"Proof with code {proof_id} not found",
        )
    # Check if the proof belongs to the current user,
    # if it doesn't, the user needs to be moderator
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
