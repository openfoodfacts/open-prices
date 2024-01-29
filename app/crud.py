import random
import string
from mimetypes import guess_extension

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func

from app import config
from app.enums import LocationOSMEnum, ProofTypeEnum
from app.models import Location, Price, Product, Proof
from app.models import Session as SessionModel
from app.models import User
from app.schemas import (
    LocationCreate,
    LocationFilter,
    LocationFull,
    PriceCreate,
    PriceFilter,
    PriceFull,
    ProductCreate,
    ProductFilter,
    ProductFull,
    ProofFilter,
    UserCreate,
)


# Users
# ------------------------------------------------------------------------------
def get_users_query(filters: ProductFilter | None = None):
    """Useful for pagination."""
    query = select(User)
    if filters:
        query = filters.filter(query)
        query = filters.sort(query)
    return query


def get_users(db: Session, filters: ProductFilter | None = None) -> list[User]:
    """Return a list of users from the database.

    :param db: the database session
    :param filters: the filters to apply to the query, defaults to None
    :return: the list of users
    """
    return db.execute(get_users_query(filters=filters)).all()


def get_user_by_user_id(db: Session, user_id: str) -> User:
    return db.query(User).filter(User.user_id == user_id).first()


def get_session_by_token(db: Session, token: str) -> SessionModel:
    """Return the session linked to the token.

    :param db: the database session
    :param token: the session token
    :return: the session
    """
    return db.query(SessionModel).join(User).filter(SessionModel.token == token).first()


def create_user(db: Session, user_id: str) -> User:
    """Create a user in the database.

    :param db: the database session
    :param user_id: the Open Food Facts user ID
    :param token: the session token
    :return: the created user
    """
    user = User(user_id=user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_session(db: Session, user: User, token: str) -> SessionModel:
    """Create a session in the database.

    :param db: the database session
    :param user: the user linked to the session
    :param token: the session token
    :return: the created session
    """
    session = SessionModel(token=token, user=user)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_session(
    db: Session, user_id: str, token: str
) -> tuple[SessionModel, User, bool]:
    """Create a new session (and optionally the user if it doesn't exist) in
    DB.

    :param db: the database session
    :param user_id: the Open Food Facts user ID
    :param token: the session token
    :return: the created session, the user and a boolean indicating whether the
        user was created or not
    """
    created = False
    user = get_user_by_user_id(db, user_id=user_id)
    if not user:
        user = create_user(db, user_id=user_id)
        session = _create_session(db, user=user, token=token)
        created = True
    else:
        session = get_session_by_token(db, token=token)
        if not session:
            session = _create_session(db, user=user, token=token)
    return session, user, created


def update_session_last_used_field(db: Session, session: SessionModel) -> SessionModel:
    """Update the last_used field of a session to the current time."""
    session.last_used = func.now()
    db.commit()
    db.refresh(session)
    return session


def increment_user_price_count(db: Session, user: UserCreate):
    """Increment the price count of a user.

    This is used to keep track of the number of prices linked to a user.
    """
    user.price_count += 1
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: UserCreate):
    db_user = get_user_by_user_id(db, user_id=user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def delete_session(db: Session, session_id: int) -> bool:
    """Delete the user session.

    :param db: the database session
    :param session_id: the DB session ID
    :return: a bool indicating whether the session was deleted
    """
    results = db.execute(
        SessionModel.__table__.delete().where(SessionModel.id == session_id)
    )
    db.commit()
    return results.rowcount > 0


# Products
# ------------------------------------------------------------------------------
def get_products_query(filters: ProductFilter | None = None):
    """Useful for pagination."""
    query = select(Product)
    if filters:
        query = filters.filter(query)
        query = filters.sort(query)
    return query


def get_products(db: Session, filters: ProductFilter | None = None):
    return db.execute(get_products_query(filters=filters)).all()


def get_product_by_id(db: Session, id: int):
    return db.query(Product).filter(Product.id == id).first()


def get_product_by_code(db: Session, code: str) -> Product:
    return db.query(Product).filter(Product.code == code).first()


def create_product(
    db: Session, product: ProductCreate, price_count: int = 0
) -> Product:
    """Create a product in the database.

    :param db: the database session
    :param product: the product to create
    :param price_count: the number of prices linked to the product, defaults
        to 0
    :return: the created product
    """
    db_product = Product(price_count=price_count, **product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_or_create_product(
    db: Session, product: ProductCreate, init_price_count: int = 0
):
    """Get or create a product in the database.

    :param db: the database session
    :param product: the product to create
    :param init_price_count: the initial number of prices linked to the
        product if a product is created, defaults to 0
    :return: the created product and a boolean indicating whether the product
        was created or not
    """
    created = False
    db_product = get_product_by_code(db, code=product.code)
    if not db_product:
        db_product = create_product(db, product=product, price_count=init_price_count)
        created = True
    return db_product, created


def update_product(db: Session, product: ProductFull, update_dict: dict):
    for key, value in update_dict.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def increment_product_price_count(db: Session, product: ProductFull):
    """Increment the price count of a product.

    This is used to keep track of the number of prices linked to a product.
    """
    product.price_count += 1
    db.commit()
    db.refresh(product)
    return product


# Prices
# ------------------------------------------------------------------------------
def get_prices_query(
    with_join_product: bool = True,
    with_join_location: bool = True,
    with_join_proof: bool = True,
    filters: PriceFilter | None = None,
):
    """Useful for pagination."""
    query = select(Price)
    if with_join_product:
        query = query.options(joinedload(Price.product))
    if with_join_location:
        query = query.options(joinedload(Price.location))
    if with_join_proof:
        query = query.options(joinedload(Price.proof))
    if filters:
        query = filters.filter(query)
        query = filters.sort(query)
    return query


def get_prices(db: Session, filters: PriceFilter | None = None):
    return db.execute(get_prices_query(filters=filters)).all()


def create_price(db: Session, price: PriceCreate, user: UserCreate):
    db_price = Price(**price.model_dump(), owner=user.user_id)
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


def link_price_product(
    db: Session, price: PriceFull, product: ProductFull
) -> PriceFull:
    """Link the product DB object to the price DB object and return the updated
    price."""
    price.product_id = product.id
    db.commit()
    db.refresh(price)
    return price


def set_price_location(db: Session, price: PriceFull, location: LocationFull):
    price.location_id = location.id
    db.commit()
    db.refresh(price)
    return price


# Proofs
# ------------------------------------------------------------------------------
def get_proofs_query(filters: ProofFilter | None = None):
    """Useful for pagination."""
    query = select(Proof)
    if filters:
        query = filters.filter(query)
        query = filters.sort(query)
    return query


def get_proofs(db: Session, filters: ProofFilter | None = None):
    return db.execute(get_proofs_query(filters=filters)).all()


def get_proof(db: Session, proof_id: int):
    return db.query(Proof).filter(Proof.id == proof_id).first()


def create_proof(
    db: Session,
    file_path: str,
    mimetype: str,
    type: ProofTypeEnum,
    user: UserCreate,
    is_public: bool = True,
):
    """Create a proof in the database.

    :param db: the database session
    :param file_path: the path to the file
    :param mimetype: the mimetype of the file
    :param user: the user who uploaded the file
    :param is_public: whether the proof is public or not
    :return: the created proof
    """
    db_proof = Proof(
        file_path=file_path,
        mimetype=mimetype,
        type=type,
        owner=user.user_id,
        is_public=is_public,
    )
    db.add(db_proof)
    db.commit()
    db.refresh(db_proof)
    return db_proof


def create_proof_file(file: UploadFile) -> tuple[str, str]:
    """Create a file in the images directory with a random name and the
    correct extension.

    :param file: the file to save
    :return: the file path and the mimetype
    """
    # Generate a random name for the file
    # This name will be used to display the image to the client, so it
    # shouldn't be discoverable
    file_stem = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    # get the extension of the file, or default to .bin
    # also manage webp case: https://stackoverflow.com/a/67938698/4293684
    mimetype = file.content_type
    extension = guess_extension(mimetype)
    if not extension:
        if mimetype == "image/webp":
            extension = ".webp"
        else:
            extension = ".bin"
    # We store the images in directories containing up to 1000 images
    # Once we reach 1000 images, we create a new directory by increasing
    # the directory ID
    # This is used to prevent the base image directory from containing too many
    # files
    images_dir = config.settings.images_dir
    current_dir_id = max(
        (int(p.name) for p in images_dir.iterdir() if p.is_dir() and p.name.isdigit()),
        default=1,
    )
    current_dir_id_str = f"{current_dir_id:04d}"
    current_dir = images_dir / current_dir_id_str
    if current_dir.exists() and len(list(current_dir.iterdir())) >= 1_000:
        # if the current directory contains 1000 images, we create a new one
        current_dir_id += 1
        current_dir = images_dir / str(current_dir_id)
    current_dir.mkdir(exist_ok=True)
    full_file_path = current_dir / f"{file_stem}{extension}"
    # write the content of the file to the new file
    with full_file_path.open("wb") as f:
        f.write(file.file.read())
    # Build file_path
    file_path = f"{current_dir_id_str}/{file_stem}{extension}"
    return (file_path, mimetype)


# Locations
# ------------------------------------------------------------------------------
def get_locations_query(filters: LocationFilter | None = None):
    """Useful for pagination."""
    query = select(Location)
    if filters:
        query = filters.filter(query)
        query = filters.sort(query)
    return query


def get_locations(db: Session, filters: LocationFilter | None = None):
    return db.execute(get_locations_query(filters=filters)).all()


def get_location_by_id(db: Session, id: int):
    return db.query(Location).filter(Location.id == id).first()


def get_location_by_osm_id_and_type(
    db: Session, osm_id: int, osm_type: LocationOSMEnum
):
    return (
        db.query(Location)
        .filter(Location.osm_id == osm_id)
        .filter(Location.osm_type == osm_type)
        .first()
    )


def create_location(
    db: Session, location: LocationCreate, price_count: int = 0
) -> Location:
    """Create a location in the database.

    :param db: the database session
    :param location: the location to create
    :param price_count: the number of prices linked to the location, defaults
        to 0
    :return: the created location
    """
    db_location = Location(price_count=price_count, **location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def get_or_create_location(
    db: Session, location: LocationCreate, init_price_count: int = 0
):
    """Get or create a location in the database.

    :param db: the database session
    :param location: the location to create
    :param init_price_count: the initial number of prices linked to the
        location if a location is created, defaults to 0
    :return: the created location and a boolean indicating whether the location
        was created or not
    """
    created = False
    db_location = get_location_by_osm_id_and_type(
        db, osm_id=location.osm_id, osm_type=location.osm_type
    )
    if not db_location:
        db_location = create_location(
            db, location=location, price_count=init_price_count
        )
        created = True
    return db_location, created


def update_location(db: Session, location: LocationFull, update_dict: dict):
    for key, value in update_dict.items():
        setattr(location, key, value)
    db.commit()
    db.refresh(location)
    return location


def increment_location_price_count(db: Session, location: LocationFull):
    """Increment the price count of a location.

    This is used to keep track of the number of prices linked to a location.
    """
    location.price_count += 1
    db.commit()
    db.refresh(location)
    return location
