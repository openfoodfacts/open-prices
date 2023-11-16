from datetime import date, datetime
from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy_utils import Currency

from app.enums import LocationOSMType
from app.models import Price


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class LocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    osm_id: int = Field(gt=0)
    osm_type: LocationOSMType


class LocationBase(LocationCreate):
    id: int
    osm_name: str | None
    osm_display_name: str | None
    osm_address_postcode: str | None
    osm_address_city: str | None
    osm_address_country: str | None
    osm_lat: float | None
    osm_lon: float | None
    created: datetime
    updated: datetime | None


class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    product_code: str = Field(min_length=1, pattern="^[0-9]+$")
    price: float
    currency: str | Currency
    location_osm_id: int = Field(gt=0)
    location_osm_type: LocationOSMType
    date: date
    proof_id: int | None = None

    @field_validator("currency")
    def currency_is_valid(cls, v):
        try:
            return Currency(v).code
        except ValueError:
            raise ValueError("not a valid currency code")

    @field_serializer("currency")
    def serialize_currency(self, currency: Currency, _info):
        if type(currency) is Currency:
            return currency.code
        return currency


class PriceBase(PriceCreate):
    location_id: int | None
    # owner: str
    created: datetime


class ProofCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    file_path: str
    mimetype: str


class ProofBase(ProofCreate):
    id: int
    owner: str
    created: datetime


class PriceFilter(Filter):
    product_code: Optional[str] | None = None
    location_osm_id: Optional[int] | None = None
    location_osm_type: Optional[LocationOSMType] | None = None
    price: Optional[int] | None = None
    currency: Optional[str] | None = None
    price__gt: Optional[int] | None = None
    price__gte: Optional[int] | None = None
    price__lt: Optional[int] | None = None
    price__lte: Optional[int] | None = None
    date: Optional[str] | None = None
    date__gt: Optional[str] | None = None
    date__gte: Optional[str] | None = None
    date__lt: Optional[str] | None = None
    date__lte: Optional[str] | None = None

    class Constants(Filter.Constants):
        model = Price
