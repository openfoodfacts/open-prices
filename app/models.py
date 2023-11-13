from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.sql import func
from sqlalchemy_utils import force_auto_coercion
from sqlalchemy_utils.types.choice import ChoiceType
from sqlalchemy_utils.types.currency import CurrencyType

from app.db import Base
from app.enums import PriceLocationOSMType

force_auto_coercion()


class User(Base):
    user_id = Column(String, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)

    last_used = Column(DateTime(timezone=True))

    created = Column(DateTime(timezone=True), server_default=func.now())

    __tablename__ = "users"


class Price(Base):
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, index=True)

    price = Column(Numeric(precision=10, scale=2))
    currency = Column(CurrencyType)

    location_osm_id = Column(BigInteger, index=True)
    location_osm_type = Column(ChoiceType(PriceLocationOSMType))

    date = Column(Date)
    owner = Column(String)

    created = Column(DateTime(timezone=True), server_default=func.now())

    __tablename__ = "prices"
