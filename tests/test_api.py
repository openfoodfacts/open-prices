import datetime
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

db_session = pytest.fixture(override_get_db, scope="module")

# client setup & fixtures
# ------------------------------------------------------------------------------
client = TestClient(app)

USER = UserBase(user_id="user1", token="user1__Utoken")
PRODUCT = ProductCreate(code="8001505005592")
PRODUCT_1 = ProductCreate(
    code="0022314010025",
    product_name="Chestnut spread 500 g",
    product_quantity=500,
    brands="Clément Faugier",
    source="off",
    unique_scans_n=20,
)
PRODUCT_2 = ProductCreate(
    code="0022314010100",
    product_name="Chestnut spread 100 g",
    product_quantity=100,
    brands="Clément Faugier",
    source="off",
    unique_scans_n=10,
)
PRODUCT_3 = ProductCreate(
    code="3760091721969",
    product_name="Crème bio de châtaignes 320 g",
    product_quantity=320,
    brands="Ethiquable",
    source="off",
    unique_scans_n=0,
)
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
def user(db_session):
    db_user = crud.create_user(db_session, USER)
    return db_user


@pytest.fixture(scope="module")
def product(db_session):
    db_product = crud.create_product(db_session, PRODUCT)
    return db_product


@pytest.fixture(scope="module")
def location(db_session):
    db_location = crud.create_location(db_session, LOCATION)
    return db_location


@pytest.fixture(scope="function")
def clean_prices(db_session):
    db_session.query(crud.Price).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def clean_products(db_session):
    db_session.query(crud.Product).delete()
    db_session.commit()


# Test prices
# ------------------------------------------------------------------------------
def test_create_price(db_session, user, clean_prices):
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
    assert len(crud.get_prices(db_session)) == 1
    # assert db_prices[0]["owner"] == user.user_id


def test_create_price_with_category_tag(db_session, user, clean_prices):
    PRICE_WITH_CATEGORY_TAG = PRICE_1.model_copy(
        update={
            "product_code": None,
            "category_tag": "en:tomatoes",
            "labels_tags": ["en:Organic"],
            "origins_tags": ["en:France"],
            "date": "2023-12-01",
        }
    )
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_CATEGORY_TAG),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    json_response = response.json()
    assert response.status_code == 201
    assert json_response.get("category_tag") == "en:tomatoes"
    assert json_response.get("labels_tags") == ["en:organic"]
    assert json_response.get("origins_tags") == ["en:france"]
    assert json_response.get("date") == "2023-12-01"
    assert "id" not in response.json()
    db_prices = crud.get_prices(db_session)
    assert len(db_prices) == 1


def test_create_price_required_fields_validation(db_session, user, clean_prices):
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
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_product_code_pattern_validation(db_session, user, clean_prices):
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
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_category_tag_pattern_validation(db_session, user, clean_prices):
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
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_currency_validation(db_session, user, clean_prices):
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
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_location_osm_type_validation(db_session, user, clean_prices):
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
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_code_category_exclusive_validation(
    db_session, user, clean_prices
):
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
    assert len(crud.get_prices(db_session)) == 0
    # only product_code: ok
    PRICE_WITH_ONLY_PRODUCT_CODE = PRICE_1.model_copy()
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_ONLY_PRODUCT_CODE),
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 201
    assert len(crud.get_prices(db_session)) == 1
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
    assert len(crud.get_prices(db_session)) == 2
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
    assert len(crud.get_prices(db_session)) == 2


def test_create_price_labels_tags_pattern_validation(db_session, user, clean_prices):
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
        assert len(crud.get_prices(db_session)) == 0


def test_get_prices(db_session, user, clean_prices):
    for _ in range(3):
        crud.create_price(db_session, PRICE_1, user)

    assert len(crud.get_prices(db_session)) == 3
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    for price_field in ["owner", "product_id", "location_id", "proof_id"]:
        assert price_field in response.json()["items"][0]
    for price_relationship in ["product", "location"]:
        assert price_relationship in response.json()["items"][0]


def test_get_prices_pagination():
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    for key in ["items", "total", "page", "size", "pages"]:
        assert key in response.json()


def test_get_prices_filters(db_session, user, clean_prices):
    crud.create_price(db_session, PRICE_1, user)
    crud.create_price(
        db_session,
        PRICE_1.model_copy(
            update={
                "price": 3.99,
                "currency": "USD",
                "date": datetime.date.fromisoformat("2023-11-01"),
            }
        ),
        user,
    )
    crud.create_price(db_session, PRICE_1.model_copy(update={"price": 5.10}), user)
    crud.create_price(
        db_session,
        PRICE_1.model_copy(
            update={
                "product_code": None,
                "category_tag": "en:tomatoes",
                "labels_tags": ["en:organic"],
                "origins_tags": ["en:spain"],
            }
        ),
        user,
    )

    assert len(crud.get_prices(db_session)) == 4

    # 3 prices with the same product_code
    response = client.get(f"/api/v1/prices?product_code={PRICE_1.product_code}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    # 1 price with a category_tag
    response = client.get("/api/v1/prices?category_tag=en:tomatoes")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # 1 price with labels_tags
    response = client.get("/api/v1/prices?labels_tags__like=en:organic")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # 1 price with origins_tags
    response = client.get("/api/v1/prices?origins_tags__like=en:spain")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # 1 price with price > 5
    response = client.get("/api/v1/prices?price__gt=5")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # 1 price with currency USD
    response = client.get("/api/v1/prices?currency=USD")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # 2 prices with date = 2023-10-31
    response = client.get(f"/api/v1/prices?date={PRICE_1.date}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3


def test_get_prices_orders(db_session, user, clean_prices):
    crud.create_price(db_session, PRICE_1, user)
    crud.create_price(
        db_session,
        PRICE_1.model_copy(
            update={"price": 3.99, "date": datetime.date.fromisoformat("2023-10-01")}
        ),
        user,
    )
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-31"
    response = client.get("/api/v1/prices?order_by=date")  # ASC
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-01"
    response = client.get("/api/v1/prices?order_by=-date")  # DESC
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-31"


# Test proofs
# ------------------------------------------------------------------------------
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


# Test products
# ------------------------------------------------------------------------------
def test_get_products(db_session, clean_products):
    crud.create_product(db_session, PRODUCT_1)
    crud.create_product(db_session, PRODUCT_2)
    crud.create_product(db_session, PRODUCT_3)

    assert len(crud.get_products(db_session)) == 3
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3


def test_get_products_pagination(clean_products):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    for key in ["items", "total", "page", "size", "pages"]:
        assert key in response.json()


# def test_get_products_filters(db_session, clean_products):
#     crud.create_product(db_session, PRODUCT_1)
#     crud.create_product(db_session, PRODUCT_2)
#     crud.create_product(db_session, PRODUCT_3)

#     assert len(crud.get_products(db_session)) == 3

#     # 3 prices with the same source
#     response = client.get("/api/v1/products?source=off")
#     assert response.status_code == 200
#     assert len(response.json()["items"]) == 3
#     # 1 price with a specific product_name
#     response = client.get("/api/v1/products?product_name__like=châtaignes")
#     assert response.status_code == 200
#     assert len(response.json()["items"]) == 1
#     # 2 prices with the same brand
#     response = client.get("/api/v1/products?brands__like=Clément Faugier")
#     assert response.status_code == 200
#     assert len(response.json()["items"]) == 2
#     # 2 prices with a positive unique_scans_n
#     response = client.get("/api/v1/products?unique_scans_n__gte=1")
#     assert response.status_code == 200
#     assert len(response.json()["items"]) == 2


def test_get_product(db_session, clean_products):
    crud.create_product(db_session, PRODUCT_1)
    crud.create_product(db_session, PRODUCT_2)
    last_product = crud.create_product(db_session, PRODUCT_3)

    # by id: product exists
    response = client.get(f"/api/v1/products/{last_product.id}")
    assert response.status_code == 200
    # by id: product does not exist
    response = client.get(f"/api/v1/products/{last_product.id+1}")
    assert response.status_code == 404
    # by code: product exists
    response = client.get(f"/api/v1/products/code/{last_product.code}")
    assert response.status_code == 200
    # by code: product does not exist
    response = client.get(f"/api/v1/products/code/{last_product.code+'X'}")
    assert response.status_code == 404


# Test locations
# ------------------------------------------------------------------------------
def test_get_location(location):
    # by id: location exists
    response = client.get(f"/api/v1/locations/{location.id}")
    assert response.status_code == 200
    # by id: location does not exist
    response = client.get(f"/api/v1/locations/{location.id+1}")
    assert response.status_code == 404
    # by osm id & type: location exists
    response = client.get(
        f"/api/v1/locations/osm/{location.osm_type.value}/{location.osm_id}"
    )
    assert response.status_code == 200
    response = client.get(
        f"/api/v1/locations/osm/{location.osm_type.value.lower()}/{location.osm_id}"
    )
    assert response.status_code == 200
    # by osm id & type: location does not exist
    response = client.get(
        f"/api/v1/locations/osm/{location.osm_type.value}/{location.osm_id+1}"
    )
    assert response.status_code == 404
