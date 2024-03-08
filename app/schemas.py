import datetime
from typing import Annotated, Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from openfoodfacts import Flavor
from openfoodfacts.taxonomy import get_taxonomy
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.enums import CurrencyEnum, LocationOSMEnum, PricePerEnum, ProofTypeEnum
from app.models import Location, Price, Product, Proof, User

# Session
# ------------------------------------------------------------------------------


class SessionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    created: datetime.datetime
    last_used: datetime.datetime | None


# User
# ------------------------------------------------------------------------------
class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    price_count: int = 0
    is_moderator: bool = False


class UserCreate(UserBase):
    token: str


# Product
# ------------------------------------------------------------------------------
class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    code: str = Field(
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["8001505005707"],
    )


class ProductFull(ProductCreate):
    id: int
    source: Flavor | None = Field(
        description="source of data, either `off` (Open Food Facts), "
        "`obf` (Open Beauty Facts), `opff` (Open Pet Food Facts) or `obf` (Open Beauty Facts)"
    )
    product_name: str | None = Field(
        description="name of the product.", examples=["Nocciolata"]
    )
    product_quantity: int | None = Field(
        description="quantity of the product, normalized in g or ml (depending on the product).",
        examples=[700],
    )
    product_quantity_unit: str | None = Field(
        description="quantity unit of the product: g or ml (depending on the product).",
        examples=["g", "ml"],
    )
    categories_tags: list[str] = Field(
        description="categories of the product.",
        examples=[["en:breakfasts", "en:spreads"]],
    )
    brands: str | None = Field(
        description="brand(s) of the product.",
        examples=["Rigoni di Asiago", "Lindt"],
    )
    brands_tags: list[str] = Field(
        description="brands of the product.",
        examples=[["douceur-du-verger", "marque-repere"]],
    )
    labels_tags: list[str] = Field(
        description="labels of the product.",
        examples=[["en:fair-trade", "en:organic", "en:made-in-france"]],
    )
    image_url: AnyHttpUrl | None = Field(
        description="URL of the product image.",
        examples=[
            "https://images.openfoodfacts.org/images/products/800/150/500/5707/front_fr.161.400.jpg"
        ],
    )
    nutriscore_grade: str | None = Field(
        description="Nutriscore grade.", examples=["a", "unknown"]
    )
    unique_scans_n: int = Field(
        description="number of unique scans of the product on Open Food Facts.",
        examples=[15],
        default=0,
    )
    price_count: int = Field(
        description="number of prices for this product.", examples=[15], default=0
    )
    created: datetime.datetime = Field(description="datetime of the creation.")
    updated: datetime.datetime | None = Field(
        description="datetime of the last update."
    )


# Location
# ------------------------------------------------------------------------------
class LocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    osm_id: int = Field(gt=0)
    osm_type: LocationOSMEnum
    price_count: int = Field(
        description="number of prices for this location.", examples=[15], default=0
    )


class LocationFull(LocationCreate):
    id: int
    osm_name: str | None = None
    osm_display_name: str | None = None
    osm_address_postcode: str | None = None
    osm_address_city: str | None = None
    osm_address_country: str | None = None
    osm_lat: float | None = None
    osm_lon: float | None = None
    created: datetime.datetime
    updated: datetime.datetime | None = None


# Proof
# ------------------------------------------------------------------------------
class ProofFull(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    # file_path is str | null because we can mask the file path in the response
    # if the proof is not public
    file_path: str | None
    mimetype: str
    type: ProofTypeEnum | None = None
    owner: str
    is_public: Annotated[
        bool,
        Field(
            default=True,
            description="if true, the proof is public and is included in the API response. "
            "Set false only if the proof contains personal information.",
        ),
    ]
    price_count: int = Field(
        description="number of prices for this proof.", examples=[15], default=0
    )
    created: datetime.datetime


class ProofBasicUpdatableFields(BaseModel):
    type: ProofTypeEnum | None = None
    is_public: bool | None = None

    class Config:
        extra = "forbid"


# Price
# ------------------------------------------------------------------------------
class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    product_code: str | None = Field(
        default=None,
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["16584958", "8001505005707"],
    )
    product_name: str | None = Field(
        default=None,
        min_length=1,
        description="name of the product, as displayed on the receipt or the price tag.",
        examples=["PATE NOCCIOLATA BIO 700G"],
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
    labels_tags: list[str] | None = Field(
        default=None,
        description="""labels of the product, only for products without barcode.

        The labels must be valid labels in the Open Food Facts taxonomy.
        If one of the labels is not valid, the price will be rejected.

        The most common labels are:
        - `en:organic`: the product is organic
        - `fr:ab-agriculture-biologique`: the product is organic, in France
        - `en:fair-trade`: the product is fair-trade

        Other labels can be provided if relevant.
        """,
        examples=["en:organic", "fr:ab-agriculture-biologique", "en:fair-trade"],
    )
    origins_tags: list[str] | None = Field(
        default=None,
        description="""origins of the product, only for products without barcode.

        This field is a list as some products may be a mix of several origins,
        but most products have only one origin.

        The origins must be valid origins in the Open Food Facts taxonomy.
        If one of the origins is not valid, the price will be rejected.""",
        examples=["en:california", "en:france", "en:italy", "en:spain"],
    )
    price: float = Field(
        gt=0,
        description="price of the product, without its currency, taxes included.",
        examples=["1.99"],
    )
    price_is_discounted: bool = Field(
        default=False,
        description="true if the price is discounted.",
        examples=[True],
    )
    price_without_discount: float | None = Field(
        default=None,
        description="price of the product without discount, without its currency, taxes included. "
        "If the product is not discounted, this field must be null. ",
        examples=["2.99"],
    )
    price_per: PricePerEnum | None = Field(
        default=PricePerEnum.KILOGRAM,
        description="""if the price is about a barcode-less product
        (if `category_tag` is provided), this field must be set to `KILOGRAM`
        or `UNIT` (KILOGRAM by default).
        This field is set to null and ignored if `product_code` is provided.
        """,
    )
    currency: CurrencyEnum = Field(
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
    location_osm_type: LocationOSMEnum = Field(
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


class PriceCreateWithValidation(PriceCreate):
    """A version of `PriceCreate` with taxonomy validations.

    These validations are not done in the `PriceCreate` model because they
    they are time-consuming and only necessary when creating a price from
    the API.
    """

    @field_validator("labels_tags")
    def labels_tags_is_valid(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if len(v) == 0:
                raise ValueError("`labels_tags` cannot be empty")
            v = [label_tag.lower() for label_tag in v]
            labels_taxonomy = get_taxonomy("label")
            for label_tag in v:
                if label_tag not in labels_taxonomy:
                    raise ValueError(
                        f"Invalid label tag: label '{label_tag}' does not exist in the taxonomy",
                    )
        return v

    @field_validator("origins_tags")
    def origins_tags_is_valid(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if len(v) == 0:
                raise ValueError("`origins_tags` cannot be empty")
            v = [origin_tag.lower() for origin_tag in v]
            origins_taxonomy = get_taxonomy("origin")
            for origin_tag in v:
                if origin_tag not in origins_taxonomy:
                    raise ValueError(
                        f"Invalid origin tag: origin '{origin_tag}' does not exist in the taxonomy",
                    )
        return v

    @field_validator("category_tag")
    def category_tag_is_valid(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.lower()
            category_taxonomy = get_taxonomy("category")
            if v not in category_taxonomy:
                raise ValueError(
                    f"Invalid category tag: category '{v}' does not exist in the taxonomy"
                )
        return v

    @model_validator(mode="after")
    def product_code_and_category_tag_are_exclusive(self):  # type: ignore
        """Validator that checks that `product_code` and `category_tag` are
        exclusive, and that at least one of them is set."""
        if self.product_code is not None:
            if self.category_tag is not None:
                raise ValueError(
                    "`product_code` and `category_tag` are exclusive, you can't set both"
                )
            if self.labels_tags is not None:
                raise ValueError(
                    "`labels_tags` can only be set for products without barcode"
                )
            if self.origins_tags is not None:
                raise ValueError(
                    "`origins_tags` can only be set for products without barcode"
                )
        if self.product_code is None and self.category_tag is None:
            raise ValueError("either `product_code` or `category_tag` must be set")
        return self

    @model_validator(mode="after")
    def set_price_per_to_null_if_barcode(self):  # type: ignore
        """Validator that sets `price_per` to null if `product_code` is set."""
        if self.product_code is not None:
            self.price_per = None
        return self

    @model_validator(mode="after")
    def check_price_discount(self):  # type: ignore
        """
        Check that:
        - `price_is_discounted` is true if `price_without_discount` is passed
        - `price_without_discount` is greater than `price`
        """
        if self.price_without_discount is not None:
            if not self.price_is_discounted:
                raise ValueError(
                    "`price_is_discounted` must be true if `price_without_discount` is filled"
                )
            if self.price_without_discount <= self.price:
                raise ValueError(
                    "`price_without_discount` must be greater than `price`"
                )
        return self


class PriceBasicUpdatableFields(BaseModel):
    price: float | None = None
    price_is_discounted: bool | None = None
    price_without_discount: float | None = None
    price_per: PricePerEnum | None = None
    currency: CurrencyEnum | None = None
    date: datetime.date | None = None

    class Config:
        extra = "forbid"


class PriceFull(PriceCreate):
    id: int
    product_id: int | None
    location_id: int | None
    owner: str
    created: datetime.datetime


class PriceFullWithRelations(PriceFull):
    product: ProductFull | None
    proof: ProofFull | None
    location: LocationFull | None


# Filters
# ------------------------------------------------------------------------------
class PriceFilter(Filter):
    product_code: Optional[str] | None = None
    product_id: Optional[int] | None = None
    product_id__isnull: Optional[bool] | None = None
    category_tag: Optional[str] | None = None
    location_osm_id: Optional[int] | None = None
    location_osm_type: Optional[LocationOSMEnum] | None = None
    location_id: Optional[int] | None = None
    price: Optional[int] | None = None
    price_is_discounted: Optional[bool] | None = None
    price__gt: Optional[int] | None = None
    price__gte: Optional[int] | None = None
    price__lt: Optional[int] | None = None
    price__lte: Optional[int] | None = None
    currency: Optional[str] | None = None
    date: Optional[str] | None = None
    date__gt: Optional[str] | None = None
    date__gte: Optional[str] | None = None
    date__lt: Optional[str] | None = None
    date__lte: Optional[str] | None = None
    proof_id: Optional[int] | None = None
    owner: Optional[str] | None = None
    # created__date  # how to filter on full day ?
    created__gte: Optional[str] | None = None
    created__lte: Optional[str] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Price


class ProofFilter(Filter):
    owner: Optional[str] | None = None
    type: Optional[ProofTypeEnum] | None = None
    price_count: Optional[int] | None = None
    price_count__gte: Optional[int] | None = None
    price_count__lte: Optional[int] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Proof


class ProductFilter(Filter):
    code: Optional[str] | None = None
    source: Optional[Flavor] | None = None
    product_name__like: Optional[str] | None = None
    categories_tags__contains: Optional[str] | None = None
    labels_tags__contains: Optional[str] | None = None
    brands__like: Optional[str] | None = None
    nutriscore_grade: Optional[str] | None = None
    unique_scans_n__gte: Optional[int] | None = None
    price_count: Optional[int] | None = None
    price_count__gte: Optional[int] | None = None
    price_count__lte: Optional[int] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Product


class LocationFilter(Filter):
    osm_name__like: Optional[str] | None = None
    osm_address_country__like: Optional[str] | None = None
    price_count: Optional[int] | None = None
    price_count__gte: Optional[int] | None = None
    price_count__lte: Optional[int] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Location


class UserFilter(Filter):
    price_count: Optional[int] | None = None
    price_count__gte: Optional[int] | None = None
    price_count__lte: Optional[int] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = User
