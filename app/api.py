import functools
import time
import uuid
from pathlib import Path
from typing import Annotated, Iterator

import requests
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from openfoodfacts.utils import get_logger
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.auth import OAuth2PasswordBearerOrAuthCookie
from app.config import settings
from app.db import session
from app.enums import ProofTypeEnum
from app.models import Location, Price, Product, Proof
from app.models import Session as SessionModel
from app.models import User
from app.schemas import PriceFullWithRelations
from app.utils import init_sentry

logger = get_logger(level=settings.log_level.to_int())

description = """
Open Prices API allows you to add product prices.
"""
app = FastAPI(
    title="Open Food Facts open-prices REST API",
    description=description,
    contact={
        "name": "The Open Food Facts team",
        "url": "https://world.openfoodfacts.org",
        "email": "contact@openfoodfacts.org",
    },
    license_info={
        "name": " AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

init_sentry(settings.sentry_dns)


# App database
# ------------------------------------------------------------------------------
def get_db() -> Iterator[Session]:
    db = session()
    try:
        yield db
    finally:
        db.close()


# Authentication helpers
# ------------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearerOrAuthCookie(tokenUrl="auth")
# Version of oauth2_scheme that does not raise an error if the token is
# invalid or missing
oauth2_scheme_no_error = OAuth2PasswordBearerOrAuthCookie(
    tokenUrl="auth", auto_error=False
)


def create_token(user_id: str) -> str:
    return f"{user_id}__U{str(uuid.uuid4())}"


def get_current_session(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> SessionModel:
    """Get the current user session, if authenticated.

    This function is used as a dependency in endpoints that require
    authentication. It raises an HTTPException if the user is not
    authenticated.

    :param token: the authentication token
    :param db: the database session
    :raises HTTPException: if the user is not authenticated
    :return: the current user session
    """
    if token and "__U" in token:
        session = crud.get_session_by_token(db, token=token)
        if session:
            return crud.update_session_last_used_field(db, session=session)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> User:
    """Get the current user if authenticated.

    This function is used as a dependency in endpoints that require
    authentication. It raises an HTTPException if the user is not
    authenticated.

    :param token: the authentication token
    :param db: the database session
    :raises HTTPException: if the user is not authenticated
    :return: the current user
    """
    if token and "__U" in token:
        session = crud.get_session_by_token(db, token=token)
        if session:
            return crud.update_session_last_used_field(db, session=session).user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_optional(
    token: Annotated[str, Depends(oauth2_scheme_no_error)],
    db: Session = Depends(get_db),
) -> User | None:
    """Get the current user if authenticated, None otherwise.

    This function is used as a dependency in endpoints that require
    authentication, but where the user is optional.

    :param token: the authentication token
    :param db: the database session
    :return: the current user if authenticated, None otherwise
    """
    if token and "__U" in token:
        session = crud.get_session_by_token(db, token=token)
        if session:
            return crud.update_session_last_used_field(db, session=session).user
    return None


# Routes
# ------------------------------------------------------------------------------
@app.get("/api/v1/status")
def status_endpoint() -> dict[str, str]:
    return {"status": "running"}


# Routes: Auth
# ------------------------------------------------------------------------------
@app.post("/api/v1/auth", tags=["Auth"])
def authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    set_cookie: Annotated[
        bool,
        Query(
            description="if set to 1, the token is also set as a cookie "
            "named 'session' in the response. This parameter must be passed "
            "as a query parameter, e.g.: /auth?set_cookie=1"
        ),
    ] = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Authentication: provide username/password and get a bearer token in return.

    - **username**: Open Food Facts user_id (not email)
    - **password**: user password (clear text, but HTTPS encrypted)

    A **token** is returned. If the **set_cookie** parameter is set to 1,
    the token is also set as a cookie named "session" in the response.

    To authenticate, you can either:
    - use the **Authorization** header with the **Bearer** scheme,
      e.g.: "Authorization: bearer token"
    - use the **session** cookie, e.g.: "Cookie: session=token"
    """
    if "oauth2_server_url" not in settings.model_dump():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAUTH2_SERVER_URL environment variable missing",
        )

    # By specifying body=1, information about the user is returned in the
    # response, including the user_id
    data = {"user_id": form_data.username, "password": form_data.password, "body": 1}
    r = requests.post(f"{settings.oauth2_server_url}", data=data)
    if r.status_code == 200:
        # form_data.username can be the user_id or the email, so we need to
        # fetch the user_id from the response
        user_id = r.json()["user_id"]
        token = create_token(user_id)
        session, *_ = crud.create_session(db, user_id=user_id, token=token)
        session = crud.update_session_last_used_field(db, session=session)
        # set the cookie if requested
        if set_cookie:
            # Don't add httponly=True or secure=True as it's still in
            # development phase, but it should be added once the front-end
            # is ready
            response.set_cookie(key="opsession", value=token)
        return {"access_token": token, "token_type": "bearer"}
    elif r.status_code == 403:
        time.sleep(2)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
    )


@app.get("/api/v1/session", response_model=schemas.SessionBase, tags=["Auth"])
def get_user_session(
    current_session: SessionModel = Depends(get_current_session),
) -> SessionModel:
    """Return information about the current user session."""
    return current_session


@app.delete("/api/v1/session", tags=["Auth"])
def delete_user_session(
    current_session: SessionModel = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete the current user session.

    If the provided session token or cookie is invalid, a HTTP 401 response
    is returned.
    """
    crud.delete_session(db, current_session.id)
    return {"status": "ok"}


# Routes: Users
# ------------------------------------------------------------------------------
@app.get("/api/v1/users", response_model=Page[schemas.UserBase], tags=["Users"])
def get_users(
    db: Session = Depends(get_db),
    filters: schemas.UserFilter = FilterDepends(schemas.UserFilter),
) -> Select[tuple[User]]:
    return paginate(db, crud.get_users_query(filters=filters))


# Routes: Prices
# ------------------------------------------------------------------------------
def price_transformer(
    prices: list[PriceFullWithRelations], current_user: schemas.UserCreate | None = None
) -> list[PriceFullWithRelations]:
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
            current_user is None
            and price.proof is not None
            and price.proof.is_public is False
        ):
            price.proof.file_path = None
        elif (
            price.proof
            and price.proof.is_public is False
            and price.proof.owner != user_id
            and current_user is not None
            and not current_user.is_moderator
        ):
            price.proof.file_path = None
    return prices


@app.get(
    "/api/v1/prices",
    response_model=Page[schemas.PriceFullWithRelations],
    tags=["Prices"],
)
def get_price(
    filters: schemas.PriceFilter = FilterDepends(schemas.PriceFilter),
    db: Session = Depends(get_db),
    current_user: schemas.UserCreate | None = Depends(get_current_user_optional),
) -> list[Price]:
    return paginate(
        db,
        crud.get_prices_query(filters=filters),
        transformer=functools.partial(price_transformer, current_user=current_user),
    )


@app.post(
    "/api/v1/prices",
    response_model=schemas.PriceFull,
    status_code=status.HTTP_201_CREATED,
    tags=["Prices"],
)
def create_price(
    price: schemas.PriceCreateWithValidation,
    background_tasks: BackgroundTasks,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Price:
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


@app.delete(
    "/api/v1/prices/{price_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Prices"],
)
def delete_price(
    price_id: int,
    current_user: schemas.UserCreate = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
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
    return None


# Routes: Proofs
# ------------------------------------------------------------------------------
@app.get("/api/v1/proofs", response_model=Page[schemas.ProofFull], tags=["Proofs"])
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


@app.post(
    "/api/v1/proofs/upload",
    response_model=schemas.ProofFull,
    status_code=status.HTTP_201_CREATED,
    tags=["Proofs"],
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


@app.delete(
    "/api/v1/proofs/{proof_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Proofs"],
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
    db_proof = crud.get_proof_by_id(db, id=proof_id)
    # get proof
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


# Routes: Products
# ------------------------------------------------------------------------------
@app.get(
    "/api/v1/products", response_model=Page[schemas.ProductFull], tags=["Products"]
)
def get_products(
    filters: schemas.ProductFilter = FilterDepends(schemas.ProductFilter),
    db: Session = Depends(get_db),
) -> list[Product]:
    return paginate(db, crud.get_products_query(filters=filters))


@app.get(
    "/api/v1/products/code/{product_code}",
    response_model=schemas.ProductFull,
    tags=["Products"],
)
def get_product_by_code(product_code: str, db: Session = Depends(get_db)) -> Product:
    db_product = crud.get_product_by_code(db, code=product_code)
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with code {product_code} not found",
        )
    return db_product


@app.get(
    "/api/v1/products/{product_id}",
    response_model=schemas.ProductFull,
    tags=["Products"],
)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)) -> Product:
    db_product = crud.get_product_by_id(db, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {product_id} not found",
        )
    return db_product


# Routes: Locations
# ------------------------------------------------------------------------------
@app.get(
    "/api/v1/locations", response_model=Page[schemas.LocationFull], tags=["Locations"]
)
def get_locations(
    filters: schemas.LocationFilter = FilterDepends(schemas.LocationFilter),
    db: Session = Depends(get_db),
) -> list[Location]:
    return paginate(db, crud.get_locations_query(filters=filters))


@app.get(
    "/api/v1/locations/osm/{location_osm_type}/{location_osm_id}",
    response_model=schemas.LocationFull,
    tags=["Locations"],
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


@app.get(
    "/api/v1/locations/{location_id}",
    response_model=schemas.LocationFull,
    tags=["Locations"],
)
def get_location_by_id(location_id: int, db: Session = Depends(get_db)) -> Location:
    db_location = crud.get_location_by_id(db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {location_id} not found",
        )
    return db_location


add_pagination(app)
