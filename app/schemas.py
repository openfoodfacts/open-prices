import datetime
from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from openfoodfacts import Flavor
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)
from sqlalchemy_utils import Currency

from app.enums import LocationOSMType
from app.models import Price


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    code: str


class ProductBase(BaseModel):
    id: int
    source: Flavor | None
    product_name: str | None
    product_quantity: int | None
    image_url: AnyHttpUrl | None
    created: datetime.datetime
    updated: datetime.datetime | None


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
    created: datetime.datetime
    updated: datetime.datetime | None


class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    product_code: str | None = Field(
        default=None,
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["16584958", "1234567890123"],
    )
    category_tag: str | None = Field(
        default=None,
        min_length=3,
        pattern=r"^[a-z]{2,}:[a-zA-Z\-]+$",
        examples=["en:tomatoes", "en:apples"],
        description="""ID of the Open Food Facts category of the product for
        products without barcode.

        This is mostly for raw products such as vegetables or fruits. This
        field is exclusive with `product_code`: if this field is set, it means
        that the product does not have a barcode.

        This ID must be a canonical category ID in the Open Food Facts taxonomy.
        If the ID is not valid, the price will be rejected.""",
    )
    price: float = Field(
        gt=0,
        description="price of the product, without its currency, taxes included.",
        examples=["1.99"],
    )
    currency: str | Currency = Field(
        description="currency of the price, as a string. "
        "The currency must be a valid currency code. "
        "See https://en.wikipedia.org/wiki/ISO_4217 for a list of valid currency codes.",
        examples=["EUR", "USD"],
    )
    location_osm_id: int = Field(
        gt=0,
        description="ID of the location in OpenStreetMap: the store where the product was bought.",
        examples=[1234567890],
    )
    location_osm_type: LocationOSMType = Field(
        description="type of the OpenStreetMap location object. Stores can be represented as nodes, "
        "ways or relations in OpenStreetMap. It is necessary to be able to fetch the correct "
        "information about the store using the ID.",
    )
    date: datetime.date = Field(description="date when the product was bought.")
    proof_id: int | None = Field(
        default=None,
        description="ID of the proof, if any. The proof is a file (receipt or price tag image) "
        "uploaded by the user to prove the price of the product. "
        "The proof must be uploaded before the price, and the authenticated user must be the "
        "owner of the proof.",
        examples=[15],
    )

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

    @model_validator(mode="after")
    def product_code_and_category_tag_are_exclusive(self):
        """Validator that checks that `product_code` and `category_tag` are
        exclusive, and that at least one of them is set."""
        if self.product_code is not None and self.category_tag is not None:
            raise ValueError(
                "`product_code` and `category_tag` are exclusive, you can't set both"
            )
        if self.product_code is None and self.category_tag is None:
            raise ValueError("either `product_code` or `category_tag` must be set")
        return self


class PriceBase(PriceCreate):
    product_id: int | None
    location_id: int | None
    # owner: str
    created: datetime.datetime


class ProofCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    file_path: str
    mimetype: str


class ProofBase(ProofCreate):
    id: int
    owner: str
    created: datetime.datetime


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
