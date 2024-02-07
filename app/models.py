from openfoodfacts import Flavor
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import force_auto_coercion
from sqlalchemy_utils.types.choice import ChoiceType

from app.db import Base
from app.enums import CurrencyEnum, LocationOSMEnum, PricePerEnum, ProofTypeEnum

force_auto_coercion()
JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class User(Base):
    user_id: str = Column(String, primary_key=True, index=True)
    price_count: int = Column(Integer, nullable=False, server_default="0", index=True)
    created = Column(DateTime(timezone=True), server_default=func.now())
    is_moderator: bool = Column(Boolean, nullable=False, server_default="false")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")

    __tablename__ = "users"


class Session(Base):
    id: int = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, ForeignKey("users.user_id"), index=True, nullable=False)
    user: Mapped[User] = relationship("User")

    token = Column(String, unique=True, index=True, nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)

    __tablename__ = "sessions"


class Product(Base):
    id: int = Column(Integer, primary_key=True, index=True)

    code: str = Column(String, unique=True, index=True)

    source: Flavor = Column(ChoiceType(Flavor))
    product_name: str = Column(String)
    product_quantity: int = Column(Integer)
    brands: str = Column(String)
    image_url: str = Column(String)
    unique_scans_n = Column(Integer, nullable=False, server_default="0")

    prices: Mapped[list["Price"]] = relationship(back_populates="product")
    price_count: int = Column(Integer, nullable=False, server_default="0", index=True)

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    __tablename__ = "products"


class Location(Base):
    id = Column(Integer, primary_key=True, index=True)

    osm_id = Column(BigInteger)
    osm_type: LocationOSMEnum = Column(ChoiceType(LocationOSMEnum))
    osm_name = Column(String)
    osm_display_name = Column(String)
    osm_address_postcode = Column(String)
    osm_address_city = Column(String)
    osm_address_country = Column(String)
    osm_lat = Column(Numeric(precision=11, scale=7))
    osm_lon = Column(Numeric(precision=11, scale=7))

    prices: Mapped[list["Price"]] = relationship(back_populates="location")
    price_count: int = Column(Integer, nullable=False, server_default="0", index=True)

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    __tablename__ = "locations"


class Proof(Base):
    id = Column(Integer, primary_key=True, index=True)

    file_path = Column(String, nullable=False)
    mimetype = Column(String, index=True)

    type: ProofTypeEnum = Column(ChoiceType(ProofTypeEnum))
    is_public = Column(Boolean, nullable=False, server_default="true", index=True)

    prices: Mapped[list["Price"]] = relationship(back_populates="proof")
    price_count: int = Column(Integer, nullable=False, server_default="0", index=True)

    owner = Column(String, index=True)

    created = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __tablename__ = "proofs"


class Price(Base):
    id = Column(Integer, primary_key=True, index=True)

    product_code = Column(String, nullable=True, index=True)
    product_name = Column(String, nullable=True)
    category_tag = Column(String, nullable=True, index=True)
    labels_tags = Column(JSONVariant, nullable=True, index=True)
    origins_tags = Column(JSONVariant, nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)
    product: Mapped[Product] = relationship(back_populates="prices")

    price = Column(Numeric(precision=10, scale=2))
    price_is_discounted = Column(Boolean, nullable=False, server_default="false")
    price_without_discount = Column(Numeric(precision=10, scale=2), nullable=True)
    currency: CurrencyEnum = Column(ChoiceType(CurrencyEnum))
    price_per: PricePerEnum = Column(ChoiceType(PricePerEnum))

    location_osm_id = Column(BigInteger, index=True)
    location_osm_type: LocationOSMEnum = Column(ChoiceType(LocationOSMEnum))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=True)
    location: Mapped[Location] = relationship(back_populates="prices")

    date = Column(Date)

    proof_id: Mapped[int] = mapped_column(ForeignKey("proofs.id"), nullable=True)
    proof: Mapped[Proof] = relationship(back_populates="prices")

    owner: str = Column(String)

    created = Column(DateTime(timezone=True), server_default=func.now())

    __tablename__ = "prices"
