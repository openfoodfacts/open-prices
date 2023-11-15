import asyncio
import uuid
from datetime import date
from pathlib import Path
from typing import Annotated

import requests
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from openfoodfacts.utils import get_logger

from app import crud, schemas
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
add_pagination(app)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
init_sentry(settings.sentry_dns)


# Authentication helpers
# ------------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


async def create_token(user_id: str):
    return f"{user_id}__U{str(uuid.uuid4())}"


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    if token and "__U" in token:
        current_user: schemas.UserBase = crud.update_user_last_used_field(db, token=token)  # type: ignore
        if current_user:
            return current_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# App startup & shutdown
# ------------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    global db
    db = session()


@app.on_event("shutdown")
async def shutdown():
    db.close()


# Routes
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.post("/auth")
async def authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
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
        user: schemas.UserBase = {"user_id": form_data.username, "token": token}  # type: ignore
        crud.create_user(db, user=user)  # type: ignore
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


@app.get("/prices", response_model=list[schemas.PriceBase])
async def get_price(
    product_code: str | None = None,
    location_osm_id: int | None = None,
    date: date | None = None,
):
    filters = {
        "product_code": product_code,
        "location_osm_id": location_osm_id,
        "date": date,
    }
    db_prices = crud.get_prices(db, filters=filters)  # type: ignore
    return db_prices


@app.post("/prices", response_model=schemas.PriceBase)
async def create_price(
    price: schemas.PriceCreate,
    current_user: schemas.UserBase = Depends(get_current_user),
):
    db_price = crud.create_price(db, price=price, user=current_user)  # type: ignore
    return db_price


@app.get("/status")
async def status_endpoint():
    return {"status": "running"}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return """User-agent: *\nDisallow: /"""
