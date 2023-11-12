from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

from app.enums import PriceLocationOSMType


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_code: str
    price: float
    currency: str = "EUR"
    location_osm_id: int
    location_osm_type: PriceLocationOSMType
    date: date

    @field_validator("location_osm_id")
    def location_osm_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("must be positive")
        return v


class PriceBase(PriceCreate):
    created: datetime
