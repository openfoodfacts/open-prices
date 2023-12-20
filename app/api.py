import time
import uuid
from pathlib import Path
from typing import Annotated

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
from openfoodfacts.taxonomy import get_taxonomy
from openfoodfacts.utils import get_logger
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.auth import OAuth2PasswordBearerOrAuthCookie
from app.config import settings
from app.db import session
from app.enums import ProofTypeEnum
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
def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


# Authentication helpers
# ------------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearerOrAuthCookie(tokenUrl="auth")


def create_token(user_id: str):
    return f"{user_id}__U{str(uuid.uuid4())}"


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
):
    if token and "__U" in token:
        current_user: schemas.UserBase = crud.update_user_last_used_field(
            db, token=token
        )
        if current_user:
            return current_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Routes
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
):
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

    data = {"user_id": form_data.username, "password": form_data.password}
    r = requests.post(settings.oauth2_server_url, data=data)  # type: ignore
    if r.status_code == 200:
        token = create_token(form_data.username)
        user = schemas.UserBase(user_id=form_data.username, token=token)
        crud.create_user(db, user=user)

        # set the cookie if requested
        if set_cookie:
            # Don't add httponly=True or secure=True as it's still in
            # development phase, but it should be added once the front-end
            # is ready
            response.set_cookie(key="session", value=token)

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


@app.get("/api/v1/prices", response_model=Page[schemas.PriceFull], tags=["Prices"])
def get_price(
    filters: schemas.PriceFilter = FilterDepends(schemas.PriceFilter),
    db: Session = Depends(get_db),
):
    return paginate(db, crud.get_prices_query(filters=filters))


@app.post(
    "/api/v1/prices",
    response_model=schemas.PriceBase,
    status_code=status.HTTP_201_CREATED,
    tags=["Prices"],
)
def create_price(
    price: schemas.PriceCreate,
    background_tasks: BackgroundTasks,
    current_user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new price.

    This endpoint requires authentication.
    """
    # check if we have a proof_id provided
    if price.proof_id is not None:
        proof = crud.get_proof(db, price.proof_id)
        if proof is None:
            # No proof exists with this id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proof not found",
            )
        else:
            # Check if the proof belongs to the current user
            # Only proof uploaded by the user can be used
            if proof.owner != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Proof does not belong to current user",
                )

    if price.category_tag is not None:
        # lowercase the category tag to perform the match
        price.category_tag = price.category_tag.lower()
        category_taxonomy = get_taxonomy("category")
        if price.category_tag not in category_taxonomy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category tag: category '{price.category_tag}' does not exist in the taxonomy",
            )

    if price.labels_tags is not None:
        # lowercase the labels tags to perform the match
        price.labels_tags = [label_tag.lower() for label_tag in price.labels_tags]
        labels_taxonomy = get_taxonomy("label")
        for label_tag in price.labels_tags:
            if label_tag not in labels_taxonomy:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid label tag: label '{label_tag}' does not exist in the taxonomy",
                )

    db_price = crud.create_price(db, price=price, user=current_user)
    background_tasks.add_task(tasks.create_price_product, db, db_price)
    background_tasks.add_task(tasks.create_price_location, db, db_price)
    return db_price


@app.post(
    "/api/v1/proofs/upload",
    response_model=schemas.ProofBase,
    status_code=status.HTTP_201_CREATED,
    tags=["Proofs"],
)
def upload_proof(
    file: UploadFile,
    type: ProofTypeEnum = Form(),
    current_user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a proof file.

    The POST request must be a multipart/form-data request with a file field
    named "file".

    This endpoint requires authentication.
    """
    file_path, mimetype = crud.create_proof_file(file)
    db_proof = crud.create_proof(db, file_path, mimetype, type=type, user=current_user)
    return db_proof


@app.get("/api/v1/proofs", response_model=list[schemas.ProofBase], tags=["Proofs"])
def get_user_proofs(
    current_user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all the proofs uploaded by the current user.

    This endpoint requires authentication.
    """
    return crud.get_user_proofs(db, user=current_user)


@app.get(
    "/api/v1/products/{product_id}",
    response_model=schemas.ProductBase,
    tags=["Products"],
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_id(db, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {product_id} not found",
        )
    return db_product


@app.get(
    "/api/v1/locations/{location_id}",
    response_model=schemas.LocationBase,
    tags=["Locations"],
)
def get_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.get_location_by_id(db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {location_id} not found",
        )
    return db_location


@app.get("/api/v1/status")
def status_endpoint():
    return {"status": "running"}


add_pagination(app)
