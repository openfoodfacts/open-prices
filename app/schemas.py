from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy_utils import Currency

from app.enums import PriceLocationOSMType


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    product_code: str = Field(min_length=1, pattern="^[0-9]+$")
    price: float
    currency: str | Currency
    location_osm_id: int = Field(gt=0)
    location_osm_type: PriceLocationOSMType
    date: date

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
    # owner: str
    created: datetime
