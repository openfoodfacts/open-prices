from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models import Price, User
from app.schemas import PriceCreate, UserBase


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


def get_prices(db: Session, filters={}):
    query = db.query(Price)
    if filters.get("product_code", None):
        query = query.filter(Price.product_code == filters["product_code"])
    if filters.get("location_osm_id", None):
        query = query.filter(Price.location_osm_id == filters["location_osm_id"])
    if filters.get("date", None):
        query = query.filter(Price.date == filters["date"])
    return query.all()


def create_price(db: Session, price: PriceCreate, user: UserBase):
    db_price = Price(**price.dict(), owner=user.user_id)
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price
