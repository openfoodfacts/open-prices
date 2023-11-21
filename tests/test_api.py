import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud
from app.api import app, get_db
from app.db import Base
from app.schemas import LocationCreate, PriceCreate, UserBase

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
LOCATION = LocationCreate(osm_id=3344841823, osm_type="NODE")
PRICE_1 = PriceCreate(
    product_code="1111111111111",
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
def location(db=override_get_db()):
    db_location = crud.create_location(next(db), LOCATION)
    return db_location


# Tests
# ------------------------------------------------------------------------------
def test_hello():
    response = client.get("/")
    assert response.status_code == 200


def test_create_price(user, db=override_get_db()):
    # without authentication
    response = client.post(
        "/prices",
        json=jsonable_encoder(PRICE_1),
    )
    assert response.status_code == 401
    # with authentication
    response = client.post(
        "/prices",
        json=jsonable_encoder(PRICE_1),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json()["product_code"] == PRICE_1.product_code
    assert "id" not in response.json()
    assert "owner" not in response.json()
    db_prices = crud.get_prices(next(db))
    assert len(db_prices) == 1
    # assert db_prices[0]["owner"] == user.user_id


def test_create_price_validation(user):
    for price_field in [
        "product_code",
        "price",
        "location_osm_id",
        "location_osm_type",
        "date",
    ]:
        PRICE_WITH_FIELD_MISSING = PRICE_1.model_copy(update={price_field: None})
        response = client.post(
            "/prices",
            json=jsonable_encoder(PRICE_WITH_FIELD_MISSING),
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert response.status_code == 422


def test_get_prices():
    response = client.get("/prices")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    for price_field in ["location_id", "proof_id"]:
        assert price_field in response.json()["items"][0]


def test_get_prices_pagination():
    response = client.get("/prices")
    assert response.status_code == 200
    for key in ["items", "total", "page", "size", "pages"]:
        assert key in response.json()


def test_get_prices_filters():
    response = client.get(f"/prices?product_code={PRICE_1.product_code}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    response = client.get("/prices?price__gt=5")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
    response = client.get("/prices?date=2023-10-31")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_get_proofs(user):
    # without authentication
    response = client.get("/proofs")
    assert response.status_code == 401
    # with authentication
    response = client.get(
        "/proofs",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200


def test_get_location(location):
    # location exists
    response = client.get(f"/locations/{location.id}")
    assert response.status_code == 200
    # location does not exist
    response = client.get(f"/locations/{location.id+1}")
    assert response.status_code == 404
