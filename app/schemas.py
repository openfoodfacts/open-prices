import re
from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer
from pydantic import field_validator
from sqlalchemy_utils import Currency

from app.enums import PriceLocationOSMType


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    product_code: str = Field(min_length=1)
    price: float
    currency: str | Currency
    location_osm_id: int
    location_osm_type: PriceLocationOSMType
    date: date

    @field_validator("product_code")
    def product_code_must_be_only_numbers(cls, v):
        regex = r"^[0-9]+$"
        if not re.match(regex, v):
            raise ValueError("must only contain numbers")
        return v

    @field_validator("currency")
    def currency_is_valid(cls, v):
        try:
            return Currency(v).code
        except ValueError:
            raise ValueError("not a valid currency code")

    @field_validator("location_osm_id")
    def location_osm_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("must be positive")
        return v

    @field_serializer("currency")
    def serialize_currency(self, currency: Currency, _info):
        if type(currency) is Currency:
            return currency.code
        return currency


class PriceBase(PriceCreate):
    # owner: str
    created: datetime
