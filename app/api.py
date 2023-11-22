import asyncio
import uuid
from pathlib import Path
from typing import Annotated

import requests
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from openfoodfacts.utils import get_logger
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.config import settings
from app.db import session
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


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
@app.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.post("/auth")
def authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    Authentication: provide username/password and get a bearer token in return

    - **username**: Open Food Facts user_id (not email)
    - **password**: user password (clear text, but HTTPS encrypted)

    a **token** is returned
    to be used in requests with usual "Authorization: bearer token" header
    """
    if "oauth2_server_url" not in settings.model_dump():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAUTH2_SERVER_URL environment variable missing",
        )

    data = {"user_id": form_data.username, "password": form_data.password}
    r = requests.post(settings.oauth2_server_url, data=data)  # type: ignore
    if r.status_code == 200:
        token = await create_token(form_data.username)
        user = schemas.UserBase(user_id=form_data.username, token=token)
        crud.create_user(db, user=user)
        return {"access_token": token, "token_type": "bearer"}
    elif r.status_code == 403:
        await asyncio.sleep(2)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
    )


@app.get("/prices", response_model=Page[schemas.PriceBase])
def get_price(
    filters: schemas.PriceFilter = FilterDepends(schemas.PriceFilter),
    db: Session = Depends(get_db),
):
    return paginate(db, crud.get_prices_query(filters=filters))


@app.post("/prices", response_model=schemas.PriceBase)
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
    db_price = crud.create_price(db, price=price, user=current_user)
    background_tasks.add_task(tasks.create_price_product, db, db_price)
    background_tasks.add_task(tasks.create_price_location, db, db_price)
    return db_price


@app.post("/proofs/upload", response_model=schemas.ProofBase)
def upload_proof(
    file: UploadFile,
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
    db_proof = crud.create_proof(db, file_path, mimetype, user=current_user)
    return db_proof


@app.get("/proofs", response_model=list[schemas.ProofBase])
def get_user_proofs(
    current_user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all the proofs uploaded by the current user.

    This endpoint requires authentication.
    """
    return crud.get_user_proofs(db, user=current_user)


@app.get("/products/{product_id}", response_model=schemas.ProductBase)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_id(db, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {product_id} not found",
        )
    return db_product


@app.get("/locations/{location_id}", response_model=schemas.LocationBase)
def get_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.get_location_by_id(db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {location_id} not found",
        )
    return db_location


@app.get("/status")
def status_endpoint():
    return {"status": "running"}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return """User-agent: *\nDisallow: /"""


add_pagination(app)
