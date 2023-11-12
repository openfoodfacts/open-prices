from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from openfoodfacts.utils import get_logger

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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


@app.on_event("startup")
async def startup():
    global db
    db = session()


@app.on_event("shutdown")
async def shutdown():
    db.close()


@app.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return """User-agent: *\nDisallow: /"""
