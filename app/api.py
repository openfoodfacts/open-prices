from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from openfoodfacts.utils import get_logger

from app.config import settings
from app.routers.auth import auth_router, session_router
from app.routers.locations import router as locations_router
from app.routers.prices import router as prices_router
from app.routers.products import router as products_router
from app.routers.proofs import router as proofs_router
from app.routers.users import router as users_router
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


app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(session_router, prefix="/api/v1", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1", tags=["Users"])
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


# Extra routes
# ------------------------------------------------------------------------------
@app.get("/api/v1/status", tags=["Status"])
def status_endpoint():
    return {"status": "running"}


add_pagination(app)
