from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from openfoodfacts.utils import get_logger
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.db import get_db
from app.utils import init_sentry
from app.views.auth import auth_router, session_router
from app.views.locations import router as locations_router
from app.views.prices import router as prices_router
from app.views.products import router as products_router
from app.views.proofs import router as proofs_router

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


app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(session_router, prefix="/api/v1", tags=["Auth"])
app.include_router(locations_router, prefix="/api/v1", tags=["Locations"])
app.include_router(products_router, prefix="/api/v1", tags=["Products"])
app.include_router(proofs_router, prefix="/api/v1", tags=["Proofs"])
app.include_router(prices_router, prefix="/api/v1", tags=["Prices"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

init_sentry(settings.sentry_dns)


# Routes
# ------------------------------------------------------------------------------
@app.get("/api/v1/status", tags=["Status"])
def status_endpoint():
    return {"status": "running"}


# Routes: Users
# ------------------------------------------------------------------------------
@app.get("/api/v1/users", response_model=Page[schemas.UserBase], tags=["Users"])
def get_users(
    db: Session = Depends(get_db),
    filters: schemas.UserFilter = FilterDepends(schemas.UserFilter),
):
    return paginate(db, crud.get_users_query(filters=filters))


add_pagination(app)
