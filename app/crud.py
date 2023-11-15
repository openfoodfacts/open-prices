from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserBase


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


def delete_user(db: Session, user_id: UserBase):
    db_user = get_user_by_user_id(db, user_id=user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False
