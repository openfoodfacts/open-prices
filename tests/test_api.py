import io

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud
from app.api import app, get_db
from app.db import Base
from app.schemas import LocationCreate, PriceCreate, ProductCreate, UserBase

# database setup
# ------------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# client setup & fixtures
# ------------------------------------------------------------------------------
client = TestClient(app)

USER = UserBase(user_id="user1", token="user1__Utoken")
PRODUCT = ProductCreate(code="8001505005592")
LOCATION = LocationCreate(osm_id=3344841823, osm_type="NODE")
PRICE_1 = PriceCreate(
    product_code="8001505005707",
    product_name="PATE NOCCIOLATA BIO 700G",
    # category="en:tomatoes",
    price=3.5,
    currency="EUR",
    location_osm_id=123,
    location_osm_type="NODE",
    date="2023-10-31",
)


@pytest.fixture(scope="module")
def user(db=override_get_db()):
    db_user = crud.create_user(next(db), USER)
    return db_user


@pytest.fixture(scope="module")
def product(db=override_get_db()):
    db_product = crud.create_product(next(db), PRODUCT)
    return db_product


@pytest.fixture(scope="module")
def location(db=override_get_db()):
    db_location = crud.create_location(next(db), LOCATION)
    return db_location


# Tests
# ------------------------------------------------------------------------------
def test_create_price(user, db=override_get_db()):
    # without authentication
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_1),
    )
    assert response.status_code == 401
    # with authentication
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_1),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 201
    assert response.json()["product_code"] == PRICE_1.product_code
    assert "id" not in response.json()
    assert "owner" not in response.json()
    db_prices = crud.get_prices(next(db))
    assert len(db_prices) == 1
    # assert db_prices[0]["owner"] == user.user_id


def test_create_price_required_fields_validation(user):
    REQUIRED_FIELDS = [
        "price",
        "location_osm_id",
        "location_osm_type",
        "date",
    ]
    for price_field in REQUIRED_FIELDS:
        PRICE_WITH_FIELD_MISSING = PRICE_1.model_copy(update={price_field: None})
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_FIELD_MISSING),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_create_price_product_code_pattern_validation(user):
    # product_code cannot be an empty string, nor contain letters
    WRONG_PRICE_PRODUCT_CODES = ["", "en:tomates", "8001505005707XYZ"]
    for wrong_price_product_code in WRONG_PRICE_PRODUCT_CODES:
        PRICE_WITH_PRODUCT_CODE_ERROR = PRICE_1.model_copy(
            update={"product_code": wrong_price_product_code}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_PRODUCT_CODE_ERROR),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_create_price_category_tag_pattern_validation(user):
    # category_tag must follow a certain pattern (ex: "en:tomatoes")
    WRONG_PRICE_CATEGORY_TAGS = ["", ":", "en", ":tomatoes"]
    for wrong_price_category_tag in WRONG_PRICE_CATEGORY_TAGS:
        PRICE_WITH_CATEGORY_TAG_ERROR = PRICE_1.model_copy(
            update={"product_code": None, "category_tag": wrong_price_category_tag}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_CATEGORY_TAG_ERROR),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_create_price_currency_validation(user):
    # currency must have a specific format (ex: "EUR")
    WRONG_PRICE_CURRENCIES = ["", "€", "euro"]
    for wrong_price_currency in WRONG_PRICE_CURRENCIES:
        PRICE_WITH_CURRENCY_ERROR = PRICE_1.model_copy(
            update={"currency": wrong_price_currency}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_CURRENCY_ERROR),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_create_price_location_osm_type_validation(user):
    WRONG_PRICE_LOCATION_OSM_TYPES = ["", "node"]
    for wrong_price_location_osm_type in WRONG_PRICE_LOCATION_OSM_TYPES:
        PRICE_WITH_LOCATION_OSM_TYPE_ERROR = PRICE_1.model_copy(
            update={"location_osm_type": wrong_price_location_osm_type}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_LOCATION_OSM_TYPE_ERROR),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_create_price_code_category_exclusive_validation(user):
    # both product_code & category_tag missing: error
    PRICE_WITH_CODE_AND_CATEGORY_MISSING = PRICE_1.model_copy(
        update={"product_code": None}
    )
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_CODE_AND_CATEGORY_MISSING),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 422
    # only product_code: ok
    PRICE_WITH_ONLY_PRODUCT_CODE = PRICE_1.model_copy()
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_ONLY_PRODUCT_CODE),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 201
    # only category_tag: ok
    PRICE_WITH_ONLY_CATEGORY = PRICE_1.model_copy(
        update={
            "product_code": None,
            "category_tag": "en:tomatoes",
            "date": "2023-10-01",
        }
    )
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_ONLY_CATEGORY),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 201
    # both product_code & category_tag present: error
    PRICE_WITH_BOTH_CODE_AND_CATEGORY = PRICE_1.model_copy(
        update={"category_tag": "en:tomatoes"}
    )
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_BOTH_CODE_AND_CATEGORY),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 422


def test_create_price_labels_tags_pattern_validation(user):
    # product_code cannot be an empty string, nor contain letters
    WRONG_PRICE_LABELS_TAGS = [[]]
    for wrong_price_labels_tags in WRONG_PRICE_LABELS_TAGS:
        PRICE_WITH_LABELS_TAGS_ERROR = PRICE_1.model_copy(
            update={"labels_tags": wrong_price_labels_tags}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_LABELS_TAGS_ERROR),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_get_prices():
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    for price_field in ["product_id", "location_id", "proof_id"]:
        assert price_field in response.json()["items"][0]
    for price_relationship in ["product", "location"]:
        assert price_relationship in response.json()["items"][0]


def test_get_prices_pagination():
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    for key in ["items", "total", "page", "size", "pages"]:
        assert key in response.json()


def test_get_prices_filters():
    response = client.get(f"/api/v1/prices?product_code={PRICE_1.product_code}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    response = client.get("/api/v1/prices?price__gt=5")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
    response = client.get("/api/v1/prices?date=2023-10-31")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_prices_orders():
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-31"
    response = client.get("/api/v1/prices?order_by=date")  # ASC
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-01"
    response = client.get("/api/v1/prices?order_by=-date")  # DESC
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-31"


def test_create_proof(user):
    # without authentication
    response = client.post(
        "/api/v1/proofs/upload",
    )
    assert response.status_code == 401
    # with authentication but validation error (file & type missing)
    response = client.post(
        "/api/v1/proofs/upload",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 422
    # with authentication but validation error (type missing)
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 422
    # with authentication but validation error (file missing)
    response = client.post(
        "/api/v1/proofs/upload",
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 422
    # with authentication and no validation error
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 201


def test_get_proofs(user):
    # without authentication
    response = client.get("/api/v1/proofs")
    assert response.status_code == 401
    # with authentication
    response = client.get(
        "/api/v1/proofs",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_product(product):
    # product exists
    response = client.get(f"/api/v1/products/{product.id}")
    assert response.status_code == 200
    # product does not exist
    response = client.get(f"/api/v1/products/{product.id+1}")
    assert response.status_code == 404


def test_get_location(location):
    # location exists
    response = client.get(f"/api/v1/locations/{location.id}")
    assert response.status_code == 200
    # location does not exist
    response = client.get(f"/api/v1/locations/{location.id+1}")
    assert response.status_code == 404
