import datetime
import io

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app import crud
from app.api import app
from app.db import Base, engine, get_db, session
from app.models import Session as SessionModel
from app.schemas import LocationFull, PriceCreate, ProductFull, ProofFilter, UserCreate

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = session()
        yield db
    finally:
        # close the DB session
        db.close()


app.dependency_overrides[get_db] = override_get_db

db_session = pytest.fixture(override_get_db, scope="module")

# client setup & fixtures
# ------------------------------------------------------------------------------
client = TestClient(app)

PAGINATION_KEYS = ["items", "total", "page", "size", "pages"]

USER = UserCreate(user_id="user", token="user__Utoken")
USER_1 = UserCreate(user_id="user1", token="user1__Utoken1", price_count=0)
USER_2 = UserCreate(user_id="user2", token="user2__Utoken2", price_count=1)
PRODUCT_1 = ProductFull(
    id=1,
    code="8001505005707",
    source="off",
    product_name="Nocciolata",
    product_quantity=700,
    product_quantity_unit=None,
    categories_tags=["en:breakfasts", "en:spreads", "en:cocoa-and-hazelnuts-spreads"],
    brands="Rigoni di Asiago",
    brands_tags=["rigoni-di-asiago"],
    labels_tags=["en:no-gluten", "en:organic"],
    nutriscore_grade="d",
    ecoscore_grade="c",
    nova_group=4,
    unique_scans_n=131,
    created=datetime.datetime.now(),
    updated=datetime.datetime.now(),
)
PRODUCT_2 = ProductFull(
    id=2,
    code="0022314010100",
    source="off",
    product_name="Chestnut spread 100 g",
    product_quantity=100,
    product_quantity_unit="g",
    categories_tags=["en:spreads", "en:nuts-and-their-products"],
    brands="Clément Faugier",
    brands_tags=["clement-faugier"],
    labels_tags=[],
    nutriscore_grade="d",
    ecoscore_grade="c",
    nova_group=4,
    unique_scans_n=10,
    created=datetime.datetime.now(),
    updated=datetime.datetime.now(),
)
PRODUCT_3 = ProductFull(
    id=3,
    code="8000215204219",
    source="off",
    product_name="Vitariz Rice Drink",
    product_quantity=1000,
    product_quantity_unit=None,
    categories_tags=["en:beverages", "en:plant-based-foods"],
    brands="Vitariz, Alinor",
    brands_tags=["vitariz", "alinor"],
    labels_tags=["en:no-gluten", "en:organic", "en:no-lactose"],
    nutriscore_grade="b",
    ecoscore_grade="c",
    nova_group=None,
    unique_scans_n=2,
    created=datetime.datetime.now(),
    updated=datetime.datetime.now(),
)
LOCATION_1 = LocationFull(
    id=1,
    osm_id=652825274,
    osm_type="NODE",
    osm_name="Monoprix",
    osm_address_postcode="38000",
    osm_address_city="Grenoble",
    osm_address_country="France",
    osm_display_name="MMonoprix, Boulevard Joseph Vallier, Secteur 1, Grenoble, Isère, Auvergne-Rhône-Alpes, France métropolitaine, 38000, France",
    osm_lat=45.1805534,
    osm_lon=5.7153387,
    created=datetime.datetime.now(),
    updated=datetime.datetime.now(),
)
LOCATION_2 = LocationFull(
    id=2,
    osm_id=6509705997,
    osm_type="NODE",
    osm_name="Carrefour",
    osm_address_postcode="1000",
    osm_address_city="Bruxelles - Brussel",
    osm_address_country="België / Belgique / Belgien",
    osm_display_name="Carrefour à Bruxelles",
    osm_lat=1,
    osm_lon=2,
    created=datetime.datetime.now(),
    updated=datetime.datetime.now(),
)
PRICE_1 = PriceCreate(
    product_code="8001505005707",
    product_name="PATE NOCCIOLATA BIO 700G",
    # category="en:tomatoes",
    price=3.5,
    price_is_discounted=True,
    price_without_discount=5,
    currency="EUR",
    location_osm_id=123,
    location_osm_type="NODE",
    date="2023-10-31",
)
PRICE_2 = PriceCreate(
    product_code="8001505005707",
    product_name="PATE NOCCIOLATA BIO 700G",
    price=2.5,
    price_is_discounted=True,
    price_without_discount=3.5,
    currency="EUR",
    location_osm_id=123,
    location_osm_type="NODE",
    date="2023-10-31",
)
PRICE_3 = PriceCreate(
    product_code="8001505005707",
    product_name="PATE NOCCIOLATA BIO 700G",
    price=2.5,
    price_is_discounted=True,
    price_without_discount=3.5,
    currency="EUR",
    location_osm_id=123,
    location_osm_type="NODE",
    date="2023-10-31",
)


@pytest.fixture(scope="module")
def user(db_session):
    db_user = crud.create_user(db_session, USER.user_id)
    return db_user


@pytest.fixture(scope="module")
def user_session(db_session) -> SessionModel:
    session, *_ = crud.create_session(db_session, USER.user_id, USER.token)
    return session


@pytest.fixture()
def user_session_1(db_session) -> SessionModel:
    session, *_ = crud.create_session(db_session, USER_1.user_id, USER_1.token)
    return session


@pytest.fixture(scope="function")
def clean_users(db_session):
    db_session.query(SessionModel).delete()
    db_session.query(crud.User).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def clean_prices(db_session):
    db_session.query(crud.Price).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def clean_products(db_session):
    db_session.query(crud.Product).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def clean_locations(db_session):
    db_session.query(crud.Location).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def clean_proofs(db_session):
    db_session.query(crud.Proof).delete()
    db_session.commit()


# Test users
# ------------------------------------------------------------------------------
def test_get_users(db_session, clean_users):
    crud.create_user(db_session, USER_1.user_id)
    crud.create_user(db_session, USER_2.user_id)

    assert len(crud.get_users(db_session)) == 2
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    for user_field in ["id", "token"]:
        assert user_field not in response.json()["items"][0]
    for user_field in ["user_id", "price_count"]:
        assert user_field in response.json()["items"][0]


def test_get_users_pagination(clean_users):
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    for key in PAGINATION_KEYS:
        assert key in response.json()


def test_default_user_moderator(db_session, clean_users):
    crud.create_user(db_session, USER_1.user_id)
    assert not crud.get_user_by_user_id(db_session, USER_1.user_id).is_moderator
    crud.update_user_moderator(db_session, USER_1.user_id, True)
    assert crud.get_user_by_user_id(db_session, USER_1.user_id).is_moderator


# def test_get_users_filters(db_session, clean_users):
#     crud.create_user(db_session, USER_1)
#     crud.create_user(db_session, USER_2)

#     assert len(crud.get_users(db_session)) == 2

#     response = client.get("/api/v1/users?price_count__gte=1")
#     assert response.status_code == 200
#     assert len(response.json()["items"]) == 1


# Test prices
# ------------------------------------------------------------------------------
def test_create_price(db_session, user_session: SessionModel, clean_prices):
    # without authentication
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_1),
    )
    assert response.status_code == 401
    # with wrong authentication
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_1),
        headers={"Authorization": f"Bearer {user_session.token}X"},
    )
    assert response.status_code == 401
    # with authentication
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_1),
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201
    assert response.json()["product_code"] == PRICE_1.product_code
    assert len(crud.get_prices(db_session)) == 1
    # assert db_prices[0]["owner"] == user.user_id
    # price with discount
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_2),
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201
    assert response.json()["product_code"] == PRICE_2.product_code
    assert len(crud.get_prices(db_session)) == 1 + 1
    # assert db_prices[0]["owner"] == user.user_id


def test_create_price_moderator(db_session, user_session, user_session_1, clean_prices):
    crud.update_user_moderator(db_session, USER_1.user_id, False)
    proof = crud.create_proof(
        db_session, "/", " ", "PRICE_TAG", user_session.user, True
    )

    # user_1 is not moderator, fails to create a price with proof not owned
    assert not user_session_1.user.is_moderator
    PRICE_3.proof_id = proof.id
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_3),
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 403

    # user_1 is moderator, create a price with proof not owned
    crud.update_user_moderator(db_session, USER_1.user_id, True)
    PRICE_3.proof_id = proof.id
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_3),
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 201


def test_create_price_with_category_tag(
    db_session, user_session: SessionModel, clean_prices
):
    PRICE_WITH_CATEGORY_TAG = PRICE_1.model_copy(
        update={
            "product_code": None,
            "category_tag": "en:tomatoes",
            "labels_tags": ["en:Organic"],
            "origins_tags": ["en:France"],
            "date": "2023-12-01",
            "price_per": "UNIT",
        }
    )
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_CATEGORY_TAG),
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    json_response = response.json()
    assert response.status_code == 201
    assert json_response.get("category_tag") == "en:tomatoes"
    assert json_response.get("labels_tags") == ["en:organic"]
    assert json_response.get("origins_tags") == ["en:france"]
    assert json_response.get("date") == "2023-12-01"
    assert json_response.get("price_per") == "UNIT"
    db_prices = crud.get_prices(db_session)
    assert len(db_prices) == 1


def test_create_price_required_fields_validation(
    db_session, user_session: SessionModel, clean_prices
):
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
            headers={"Authorization": f"Bearer {user_session.token}"},
        )
        assert response.status_code == 422
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_product_code_pattern_validation(
    db_session, user_session, clean_prices
):
    # product_code cannot be an empty string, nor contain letters
    WRONG_PRICE_PRODUCT_CODES = ["", "en:tomates", "8001505005707XYZ"]
    for wrong_price_product_code in WRONG_PRICE_PRODUCT_CODES:
        PRICE_WITH_PRODUCT_CODE_ERROR = PRICE_1.model_copy(
            update={"product_code": wrong_price_product_code}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_PRODUCT_CODE_ERROR),
            headers={"Authorization": f"Bearer {user_session.token}"},
        )
        assert response.status_code == 422
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_category_tag_pattern_validation(
    db_session, user_session: SessionModel, clean_prices
):
    # category_tag must follow a certain pattern (ex: "en:tomatoes")
    WRONG_PRICE_CATEGORY_TAGS = ["", ":", "en", ":tomatoes"]
    for wrong_price_category_tag in WRONG_PRICE_CATEGORY_TAGS:
        PRICE_WITH_CATEGORY_TAG_ERROR = PRICE_1.model_copy(
            update={"product_code": None, "category_tag": wrong_price_category_tag}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_CATEGORY_TAG_ERROR),
            headers={"Authorization": f"Bearer {user_session.token}"},
        )
        assert response.status_code == 422
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_currency_validation(
    db_session, user_session: SessionModel, clean_prices
):
    # currency must have a specific format (ex: "EUR")
    WRONG_PRICE_CURRENCIES = ["", "€", "euro"]
    for wrong_price_currency in WRONG_PRICE_CURRENCIES:
        PRICE_WITH_CURRENCY_ERROR = PRICE_1.model_copy(
            update={"currency": wrong_price_currency}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_CURRENCY_ERROR),
            headers={"Authorization": f"Bearer {user_session.token}"},
        )
        assert response.status_code == 422
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_location_osm_type_validation(
    db_session, user_session: SessionModel, clean_prices
):
    WRONG_PRICE_LOCATION_OSM_TYPES = ["", "node"]
    for wrong_price_location_osm_type in WRONG_PRICE_LOCATION_OSM_TYPES:
        PRICE_WITH_LOCATION_OSM_TYPE_ERROR = PRICE_1.model_copy(
            update={"location_osm_type": wrong_price_location_osm_type}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_LOCATION_OSM_TYPE_ERROR),
            headers={"Authorization": f"Bearer {user_session.token}"},
        )
        assert response.status_code == 422
        assert len(crud.get_prices(db_session)) == 0


def test_create_price_code_category_exclusive_validation(
    db_session, user_session: SessionModel, clean_prices
):
    # both product_code & category_tag missing: error
    PRICE_WITH_CODE_AND_CATEGORY_MISSING = PRICE_1.model_copy(
        update={"product_code": None}
    )
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_CODE_AND_CATEGORY_MISSING),
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 422
    assert len(crud.get_prices(db_session)) == 0
    # only product_code: ok
    PRICE_WITH_ONLY_PRODUCT_CODE = PRICE_1.model_copy()
    response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_WITH_ONLY_PRODUCT_CODE),
        headers={"Authorization": f"Bearer {user_session.token}"},
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
        headers={"Authorization": f"Bearer {user_session.token}"},
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
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 422
    assert len(crud.get_prices(db_session)) == 2


def test_create_price_labels_tags_pattern_validation(
    db_session, user_session: SessionModel, clean_prices
):
    # product_code cannot be an empty string, nor contain letters
    WRONG_PRICE_LABELS_TAGS = [[]]
    for wrong_price_labels_tags in WRONG_PRICE_LABELS_TAGS:
        PRICE_WITH_LABELS_TAGS_ERROR = PRICE_1.model_copy(
            update={"labels_tags": wrong_price_labels_tags}
        )
        response = client.post(
            "/api/v1/prices",
            json=jsonable_encoder(PRICE_WITH_LABELS_TAGS_ERROR),
            headers={"Authorization": f"Bearer {user_session.token}"},
        )
        assert response.status_code == 422
        assert len(crud.get_prices(db_session)) == 0


def test_get_prices(db_session, user_session: SessionModel, clean_prices):
    for _ in range(3):
        crud.create_price(db_session, PRICE_1, user_session.user)

    assert len(crud.get_prices(db_session)) == 3
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    for price_field in ["owner", "product_id", "location_id", "proof_id"]:
        assert price_field in response.json()["items"][0]
    for price_relationship in ["product", "location", "proof"]:
        assert price_relationship in response.json()["items"][0]


def test_get_prices_pagination():
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    for key in PAGINATION_KEYS:
        assert key in response.json()


def test_get_prices_with_proofs(
    db_session, user_session: SessionModel, user_session_1: SessionModel, clean_prices
):
    price_tag_proof = crud.create_proof(
        db_session, "/", " ", "PRICE_TAG", user_session.user, is_public=True
    )
    receipt_proof = crud.create_proof(
        db_session, "/", " ", "PRICE_TAG", user_session.user, is_public=False
    )
    crud.create_price(db_session, PRICE_1, user_session.user)
    crud.create_price(
        db_session,
        PRICE_1.model_copy(update={"proof_id": price_tag_proof.id}),
        user_session.user,
    )
    crud.create_price(
        db_session,
        PRICE_1.model_copy(update={"proof_id": receipt_proof.id}),
        user_session.user,
    )

    # anonymous
    response = client.get("/api/v1/prices")
    assert response.json()["items"][0]["proof"]["file_path"] is not None
    assert response.json()["items"][1]["proof"]["file_path"] is None  # not public
    assert response.json()["items"][2]["proof"] is None

    # authenticated but not owner nor moderator
    crud.update_user_moderator(db_session, USER_1.user_id, False)
    response = client.get(
        "/api/v1/prices", headers={"Authorization": f"Bearer {user_session_1.token}"}
    )
    assert response.json()["items"][0]["proof"]["file_path"] is not None
    assert (
        response.json()["items"][1]["proof"]["file_path"] is None
    )  # not public, not owner
    assert response.json()["items"][2]["proof"] is None

    # authenticated and owner
    response = client.get(
        "/api/v1/prices", headers={"Authorization": f"Bearer {user_session.token}"}
    )
    assert response.json()["items"][0]["proof"]["file_path"] is not None
    assert (
        response.json()["items"][1]["proof"]["file_path"] is not None
    )  # not public, but owner
    assert response.json()["items"][2]["proof"] is None

    # authenticated and moderator
    crud.update_user_moderator(db_session, USER_1.user_id, True)
    response = client.get(
        "/api/v1/prices", headers={"Authorization": f"Bearer {user_session_1.token}"}
    )
    assert response.json()["items"][0]["proof"]["file_path"] is not None
    assert (
        response.json()["items"][1]["proof"]["file_path"] is not None
    )  # not public, not owner, but moderator
    assert response.json()["items"][2]["proof"] is None


def test_get_prices_filters(db_session, user_session: SessionModel, clean_prices):
    crud.create_price(db_session, PRICE_1, user_session.user)
    crud.create_price(
        db_session,
        PRICE_1.model_copy(
            update={
                "price": 3.99,
                "currency": "USD",
                "date": datetime.date.fromisoformat("2023-11-01"),
            }
        ),
        user_session.user,
    )
    crud.create_price(
        db_session, PRICE_1.model_copy(update={"price": 5.10}), user_session.user
    )
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
        user_session.user,
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


def test_get_prices_orders(db_session, user_session: SessionModel, clean_prices):
    # PRICE_1 date is "2023-10-31"
    crud.create_price(db_session, PRICE_1, user_session.user)
    crud.create_price(
        db_session,
        PRICE_1.model_copy(
            update={"price": 3.99, "date": datetime.date.fromisoformat("2023-10-01")}
        ),
        user_session.user,
    )
    response = client.get("/api/v1/prices")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    response = client.get("/api/v1/prices?order_by=%2Bdate")  # +date, ASC
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-01"
    response = client.get("/api/v1/prices?order_by=-date")  # DESC
    assert response.status_code == 200
    assert (response.json()["items"][0]["date"]) == "2023-10-31"


def test_update_price(db_session, user_session: SessionModel):
    db_price = crud.create_price(db_session, PRICE_1, user_session.user)
    new_price = 5.5
    PRICE_UPDATE_PARTIAL = {"price": new_price}
    # without authentication
    response = client.patch(f"/api/v1/prices/{db_price.id}")
    assert response.status_code == 401
    # with authentication but not price owner
    user_1_session, *_ = crud.create_session(db_session, USER_1.user_id, USER_1.token)
    response = client.patch(
        f"/api/v1/prices/{db_price.id}",
        headers={"Authorization": f"Bearer {user_1_session.token}"},
        json=jsonable_encoder(PRICE_UPDATE_PARTIAL),
    )
    assert response.status_code == 403
    # with authentication but price unknown
    response = client.patch(
        f"/api/v1/prices/{db_price.id+1}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PRICE_UPDATE_PARTIAL),
    )
    assert response.status_code == 404
    # with authentication and price owner
    response = client.patch(
        f"/api/v1/prices/{db_price.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PRICE_UPDATE_PARTIAL),
    )
    assert response.status_code == 200
    assert response.json()["price"] == new_price
    assert response.json()["price_is_discounted"] == PRICE_1.price_is_discounted
    assert response.json()["price_without_discount"] == PRICE_1.price_without_discount
    # with authentication and price owner
    PRICE_UPDATE_PARTIAL_MORE = {
        **PRICE_UPDATE_PARTIAL,
        "price_is_discounted": False,
        "price_without_discount": None,
    }
    response = client.patch(
        f"/api/v1/prices/{db_price.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PRICE_UPDATE_PARTIAL_MORE),
    )
    assert response.status_code == 200
    assert response.json()["price"] == new_price
    assert (
        response.json()["price_is_discounted"] != PRICE_1.price_is_discounted
    )  # False
    assert response.json()["price_without_discount"] is None
    # with authentication and price owner but extra fields
    PRICE_UPDATE_PARTIAL_WRONG = {**PRICE_UPDATE_PARTIAL, "proof_id": 1}
    response = client.patch(
        f"/api/v1/prices/{db_price.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PRICE_UPDATE_PARTIAL_WRONG),
    )
    assert response.status_code == 422


def test_delete_price(db_session, user_session: SessionModel, clean_prices):
    db_price = crud.create_price(db_session, PRICE_1, user_session.user)
    # without authentication
    response = client.delete(f"/api/v1/prices/{db_price.id}")
    assert response.status_code == 401
    # with authentication but not price owner
    user_1_session, *_ = crud.create_session(db_session, USER_1.user_id, USER_1.token)
    response = client.delete(
        f"/api/v1/prices/{db_price.id}",
        headers={"Authorization": f"Bearer {user_1_session.token}"},
    )
    assert response.status_code == 403
    # with authentication but price unknown
    response = client.delete(
        f"/api/v1/prices/{db_price.id + 1}",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 404
    # with authentication and price owner
    response = client.delete(
        f"/api/v1/prices/{db_price.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 204


# Test proofs
# ------------------------------------------------------------------------------
def test_create_proof(user_session: SessionModel, clean_proofs):
    # This test depends on the previous test_create_price
    # without authentication
    response = client.post(
        "/api/v1/proofs/upload",
    )
    assert response.status_code == 401
    # with authentication but validation error (file & type missing)
    response = client.post(
        "/api/v1/proofs/upload",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 422
    # with authentication but validation error (type missing)
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 422
    # with authentication but validation error (file missing)
    response = client.post(
        "/api/v1/proofs/upload",
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 422

    # Check that is_public = False is not allowed for types other than RECEIPT
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "PRICE_TAG", "is_public": "false"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 422

    # with authentication and no validation error
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201

    # with authentication and is_public = False
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "RECEIPT", "is_public": "false"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201


def test_get_proofs(user_session: SessionModel):
    # without authentication
    response = client.get("/api/v1/proofs")
    assert response.status_code == 401
    # with authentication
    response = client.get(
        "/api/v1/proofs",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 200

    # has pagination
    for key in PAGINATION_KEYS:
        assert key in response.json()

    data = response.json()["items"]
    assert len(data) == 2

    for item in data:
        assert set(item.keys()) == {
            "id",
            "file_path",
            "mimetype",
            "type",
            "owner",
            "created",
            "is_public",
            "price_count",
        }

    for i, item in enumerate(data):
        assert isinstance(item["id"], int)
        assert item["file_path"].startswith("0001/")
        assert item["file_path"].endswith(".webp")
        assert item["type"] == ("PRICE_TAG" if i == 0 else "RECEIPT")
        assert item["owner"] == "user"
        assert item["is_public"] == (True if i == 0 else False)
        assert item["price_count"] == 0


def test_get_proofs_filters(db_session, user_session: SessionModel):
    assert (
        len(
            crud.get_proofs(db_session, filters=ProofFilter(owner=user_session.user_id))
        )
        == 2
    )

    # 1 proof is a receipt
    response = client.get(
        "/api/v1/proofs?type=RECEIPT",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # # order by most recent  # error because same timestamp...
    # response = client.get(
    #     "/api/v1/proofs?order_by=created",
    #     headers={"Authorization": f"Bearer {user_session.token}"},
    # )
    # assert response.status_code == 200
    # assert len(response.json()["items"]) == 2
    # assert response.json()["items"][0]["id"] < response.json()["items"][1]["id"]  # noqa
    # response = client.get(
    #     "/api/v1/proofs?order_by=-created",
    #     headers={"Authorization": f"Bearer {user_session.token}"},
    # )
    # assert response.status_code == 200
    # assert len(response.json()["items"]) == 2
    # assert response.json()["items"][0]["id"] > response.json()["items"][1]["id"]  # noqa


def test_get_proof(
    db_session, user_session: SessionModel, user_session_1: SessionModel, clean_proofs
):
    proof_user = crud.create_proof(
        db_session, "/", " ", "PRICE_TAG", user_session.user, True
    )
    proof_user_1 = crud.create_proof(
        db_session, "/", " ", "RECEIPT", user_session_1.user, True
    )

    # get without auth
    response = client.get(f"/api/v1/proofs/{proof_user.id}")
    assert response.status_code == 401

    # with authentication but proof unknown
    response = client.get(
        f"/api/v1/proofs/{proof_user_1.id + 1}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 404

    # get but not proof owner and not moderator
    crud.update_user_moderator(db_session, user_session_1.user_id, False)
    response = client.get(
        f"/api/v1/proofs/{proof_user.id}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 403

    # get but not proof owner but moderator
    crud.update_user_moderator(db_session, user_session_1.user_id, True)
    response = client.get(
        f"/api/v1/proofs/{proof_user.id}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 200

    # get and proof owner
    response = client.get(
        f"/api/v1/proofs/{proof_user.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 200


def test_update_proof(
    db_session, user_session: SessionModel, user_session_1: SessionModel, clean_proofs
):
    # create proof
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201
    proof = crud.get_proof_by_id(db_session, response.json().get("id"))

    PROOF_UPDATE_PARTIAL = {"is_public": False}
    # without authentication
    response = client.patch(f"/api/v1/proofs/{proof.id}")
    assert response.status_code == 401
    # with authentication but not proof owner and not moderator
    crud.update_user_moderator(db_session, USER_1.user_id, False)
    response = client.patch(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
        json=jsonable_encoder(PROOF_UPDATE_PARTIAL),
    )
    assert response.status_code == 403
    # with authentication but proof unknown
    response = client.patch(
        f"/api/v1/proofs/{proof.id + 1}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PROOF_UPDATE_PARTIAL),
    )
    assert response.status_code == 404
    # with authentication and proof owner
    response = client.patch(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PROOF_UPDATE_PARTIAL),
    )
    assert response.status_code == 200
    assert response.json()["is_public"] is False
    assert response.json()["type"] == proof.type.value
    # with authentication and proof owner more fields
    PROOF_UPDATE_PARTIAL_MORE = {**PROOF_UPDATE_PARTIAL, "type": "RECEIPT"}
    response = client.patch(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PROOF_UPDATE_PARTIAL_MORE),
    )
    assert response.status_code == 200
    assert response.json()["is_public"] is False
    assert response.json()["type"] != proof.type.value
    # with authentication and proof owner but extra fields
    PROOF_UPDATE_PARTIAL_WRONG = {**PROOF_UPDATE_PARTIAL, "owner": 1}
    response = client.patch(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
        json=jsonable_encoder(PROOF_UPDATE_PARTIAL_WRONG),
    )
    assert response.status_code == 422


def test_delete_proof(
    db_session,
    user_session: SessionModel,
    user_session_1: SessionModel,
    clean_proofs,
    clean_prices,
):
    # create proof
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201
    proof = crud.get_proof_by_id(db_session, response.json().get("id"))
    # assert Path(images_dir/proof.file_path).exists()

    # create price associated with proof
    PRICE_3.proof_id = proof.id
    price_response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_3),
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert price_response.status_code == 201

    # delete without auth
    response = client.delete(f"/api/v1/proofs/{proof.id}")
    assert response.status_code == 401

    crud.update_user_moderator(db_session, USER_1.user_id, False)
    # delete but not proof owner and not moderator
    response = client.delete(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 403

    # with authentication but proof unknown
    response = client.delete(
        f"/api/v1/proofs/{proof.id + 1}",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 404

    # with auth but proof associated with prices
    response = client.delete(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 403
    assert len(proof.prices) > 0

    # proof without prices
    db_price = crud.get_price_by_id(db_session, price_response.json().get("id"))
    crud.delete_price(db_session, db_price)
    response = client.delete(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 204
    assert len(proof.prices) == 0
    assert crud.get_proof_by_id(db_session, proof.id) is None
    # assert not Path(images_dir/proof.file_path).exists()


def test_delete_proof_moderator(
    db_session,
    user_session: SessionModel,
    user_session_1: SessionModel,
    clean_proofs,
    clean_prices,
):
    # create proof user
    response = client.post(
        "/api/v1/proofs/upload",
        files={"file": ("filename", (io.BytesIO(b"test")), "image/webp")},
        data={"type": "PRICE_TAG"},
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert response.status_code == 201
    proof = crud.get_proof_by_id(db_session, response.json().get("id"))

    # create price associated with proof
    PRICE_3.proof_id = proof.id
    price_response = client.post(
        "/api/v1/prices",
        json=jsonable_encoder(PRICE_3),
        headers={"Authorization": f"Bearer {user_session.token}"},
    )
    assert price_response.status_code == 201

    # user_1 is moderator, not owner, but proof associated with prices
    crud.update_user_moderator(db_session, USER_1.user_id, True)
    response = client.delete(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 403

    # user_1 is moderator, not owner and proof with no prices
    db_price = crud.get_price_by_id(db_session, price_response.json().get("id"))
    crud.delete_price(db_session, db_price)
    assert len(proof.prices) == 0
    response = client.delete(
        f"/api/v1/proofs/{proof.id}",
        headers={"Authorization": f"Bearer {user_session_1.token}"},
    )
    assert response.status_code == 204
    assert crud.get_proof_by_id(db_session, proof.id) is None


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
    for key in PAGINATION_KEYS:
        assert key in response.json()


def test_get_products_filters(db_session, clean_products):
    crud.create_product(db_session, PRODUCT_1)
    crud.create_product(db_session, PRODUCT_2)
    crud.create_product(db_session, PRODUCT_3)

    assert len(crud.get_products(db_session)) == 3

    # filter by source
    response = client.get("/api/v1/products?source=off")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    # filter by product_name
    response = client.get("/api/v1/products?product_name__like=Chestnut")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # filter by brand
    response = client.get("/api/v1/products?brands__like=Clément Faugier")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # filter by category tag
    response = client.get("/api/v1/products?categories_tags__contains=en:spreads")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    # filter by label tag
    response = client.get("/api/v1/products?labels_tags__contains=en:organic")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    # filter by nutriscore
    response = client.get("/api/v1/products?nutriscore_grade=b")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # filter by ecoscore
    response = client.get("/api/v1/products?ecoscore_grade=a")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
    # filter by nova
    response = client.get("/api/v1/products?nova_group=4")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    # filter by unique_scans_n
    response = client.get("/api/v1/products?unique_scans_n__gte=10")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_product(db_session, clean_products):
    crud.create_product(db_session, PRODUCT_1)
    crud.create_product(db_session, PRODUCT_2)
    last_product = crud.create_product(db_session, PRODUCT_3)

    assert len(crud.get_products(db_session)) == 3

    # by id: product exists
    response = client.get(f"/api/v1/products/{last_product.id}")
    assert response.status_code == 200
    # by id: product does not exist
    response = client.get("/api/v1/products/99999")
    assert response.status_code == 404
    # by code: product exists
    response = client.get(f"/api/v1/products/code/{last_product.code}")
    assert response.status_code == 200
    # by code: product does not exist
    response = client.get(f"/api/v1/products/code/{last_product.code + 'X'}")
    assert response.status_code == 404


# Test locations
# ------------------------------------------------------------------------------
def test_get_locations(db_session, clean_locations):
    crud.create_location(db_session, LOCATION_1)
    crud.create_location(db_session, LOCATION_2)

    assert len(crud.get_locations(db_session)) == 2
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_locations_pagination(clean_locations):
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    for key in PAGINATION_KEYS:
        assert key in response.json()


def test_get_locations_filters(db_session, clean_locations):
    crud.create_location(db_session, LOCATION_1)
    crud.create_location(db_session, LOCATION_2)

    assert len(crud.get_locations(db_session)) == 2

    # filter by osm_name
    response = client.get("/api/v1/locations?osm_name__like=Monoprix")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    # filter by osm_address_country
    response = client.get("/api/v1/locations?osm_address_country__like=France")  # noqa
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_get_location(db_session, clean_locations):
    location = crud.create_location(db_session, LOCATION_1)

    assert len(crud.get_locations(db_session)) == 1

    # by id: location exists
    response = client.get(f"/api/v1/locations/{location.id}")
    assert response.status_code == 200
    # by id: location does not exist
    response = client.get("/api/v1/locations/99999")
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
        f"/api/v1/locations/osm/{location.osm_type.value}/{location.osm_id + 1}"
    )
    assert response.status_code == 404
