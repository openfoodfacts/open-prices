import random
import string
from mimetypes import guess_extension

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app import config
from app.models import Price, Proof, User
from app.schemas import PriceCreate, ProofBase, UserBase


def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_user_id(db: Session, user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_token(db: Session, token: str):
    return db.query(User).filter(User.token == token).first()


def create_user(db: Session, user: UserBase):
    # first we delete any existing user
    delete_user(db, user_id=user["user_id"])
    # then we (re)create a user
    db_user = User(user_id=user["user_id"], token=user["token"])
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_last_used_field(db: Session, token: str):
    db_user = get_user_by_token(db, token=token)
    if db_user:
        db.query(User).filter(User.user_id == db_user.user_id).update(
            {"last_used": func.now()}
        )
        db.commit()
        db.refresh(db_user)
        return db_user
    return False


def delete_user(db: Session, user_id: UserBase):
    db_user = get_user_by_user_id(db, user_id=user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def get_prices_query(filters: dict | None = None):
    """Useful for pagination."""
    query = select(Price)
    if filters:
        if filters.get("product_code", None):
            query = query.filter(Price.product_code == filters["product_code"])
        if filters.get("location_osm_id", None):
            query = query.filter(Price.location_osm_id == filters["location_osm_id"])
        if filters.get("date", None):
            query = query.filter(Price.date == filters["date"])
    return query


def get_prices(db: Session, filters: dict | None = None):
    return db.execute(get_prices_query(filters=filters)).all()


def create_price(db: Session, price: PriceCreate, user: UserBase):
    db_price = Price(**price.model_dump(), owner=user.user_id)
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


def get_proof(db: Session, proof_id: int):
    return db.query(Proof).filter(Proof.id == proof_id).first()


def get_user_proofs(db: Session, user: UserBase):
    return db.query(Proof).filter(Proof.owner == user.user_id).all()


def create_proof(db: Session, file_path: str, mimetype: str, user: UserBase):
    """Create a proof in the database.

    :param db: the database session
    :param file_path: the path to the file
    :param mimetype: the mimetype of the file
    :param user: the user who uploaded the file
    :return: the created proof
    """
    db_proof = Proof(file_path=file_path, mimetype=mimetype, owner=user.user_id)
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
    mimetype = file.content_type
    # get the extension of the file, or default to .bin
    extension = guess_extension(mimetype) if mimetype else ".bin"
    images_dir = config.settings.images_dir
    # We store the images in directories containing up to 1000 images
    # Once we reach 1000 images, we create a new directory by increasing
    # the directory ID
    # This is used to prevent the base image directory from containing too many
    # files
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

    file_path = f"{current_dir_id_str}/{file_stem}{extension}"
    return (file_path, mimetype)
