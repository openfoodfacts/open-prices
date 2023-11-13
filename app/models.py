from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.sql import func

from app.db import Base


class User(Base):
    user_id = Column(String, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    last_used = Column(DateTime(timezone=True))
    created = Column(DateTime(timezone=True), server_default=func.now())

    __tablename__ = "users"
