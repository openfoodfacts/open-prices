import datetime
from copy import deepcopy
from typing import Any, Optional, Tuple, Type

from fastapi_filter.contrib.sqlalchemy import Filter
from openfoodfacts import Flavor
from openfoodfacts.taxonomy import get_taxonomy
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo

from app.enums import CurrencyEnum, LocationOSMEnum, PricePerEnum, ProofTypeEnum
from app.models import Location, Price, Product, Proof, User


def partial_model(model: Type[BaseModel]):
    """
    Custom decorator to set all fields of a model as optional.
    https://stackoverflow.com/a/76560886/4293684
    """

    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> Tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new

    return create_model(
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )


# Session
# ------------------------------------------------------------------------------
class SessionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    created: datetime.datetime
    last_used: datetime.datetime | None


# User
# UserBase > UserCreate
# ------------------------------------------------------------------------------
class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    price_count: int = 0
    is_moderator: bool = False


class UserCreate(UserBase):
    token: str


# Product
# ProductCreate > ProductFull
# ------------------------------------------------------------------------------
class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    code: str = Field(
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["8001505005707"],
    )
    price_count: int = Field(
        description="number of prices for this product.", examples=[15], default=0
    )


class ProductFull(ProductCreate):
    id: int
    source: Flavor | None = Field(
        description="source of data, either `off` (Open Food Facts), "
        "`obf` (Open Beauty Facts), `opf` (Open Products Facts) or `opff` (Open Pet Food Facts",
        examples=["off", "obf", "opf", "opff", None],
        default=None,
    )
    product_name: str | None = Field(
        description="name of the product.", examples=["Nocciolata"], default=None
    )
    product_quantity: int | None = Field(
        description="quantity of the product, normalized in g or ml (depending on the product).",
        examples=[700],
        default=None,
    )
    product_quantity_unit: str | None = Field(
        description="quantity unit of the product: g or ml (depending on the product).",
        examples=["g", "ml"],
        default=None,
    )
    categories_tags: list[str] = Field(
        description="categories of the product.",
        examples=[["en:breakfasts", "en:spreads"]],
        default=list,
    )
    brands: str | None = Field(
        description="brand(s) of the product.",
        examples=["Rigoni di Asiago", "Lindt"],
        default=None,
    )
    brands_tags: list[str] = Field(
        description="brands of the product.",
        examples=[["douceur-du-verger", "marque-repere"]],
        default=list,
    )
    labels_tags: list[str] = Field(
        description="labels of the product.",
        examples=[["en:fair-trade", "en:organic", "en:made-in-france"]],
        default=list,
    )
    image_url: AnyHttpUrl | None = Field(
        description="URL of the product image.",
        examples=[
            "https://images.openfoodfacts.org/images/products/800/150/500/5707/front_fr.161.400.jpg"
        ],
        default=None,
    )
    nutriscore_grade: str | None = Field(
        description="Nutri-Score grade.",
        examples=["a", "b", "c", "d", "e", "unknown", "not-applicable"],
        default=None,
    )
    ecoscore_grade: str | None = Field(
        description="Eco-Score grade.",
        examples=["a", "b", "c", "d", "e", "unknown", "not-applicable"],
        default=None,
    )
    nova_group: int | None = Field(
        description="NOVA group.", examples=[1, 2, 3, 4], default=None
    )
    unique_scans_n: int = Field(
        description="number of unique scans of the product on Open Food Facts.",
        examples=[15],
        default=0,
    )
    created: datetime.datetime = Field(description="datetime of the creation.")
    updated: datetime.datetime | None = Field(
        description="datetime of the last update.", default=None
    )


# Location
# LocationCreate > LocationFull
# ------------------------------------------------------------------------------
class LocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    osm_id: int = Field(gt=0)
    osm_type: LocationOSMEnum


class LocationFull(LocationCreate):
    id: int
    osm_name: str | None = None
    osm_display_name: str | None = None
    osm_tag_key: str | None = Field(
        description="OSM tag key", examples=["shop", "amenity"], default=None
    )
    osm_tag_value: str | None = Field(
        description="OSM tag value", examples=["supermarket", "cafe"], default=None
    )
    osm_address_postcode: str | None = None
    osm_address_city: str | None = None
    osm_address_country: str | None = None
    osm_address_country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
        description="OSM country code (ISO 3166-1 alpha-2)",
        examples=["FR", "US"],
    )
    osm_lat: float | None = None
    osm_lon: float | None = None
    price_count: int = Field(
        description="number of prices for this location.", examples=[15], default=0
    )
    created: datetime.datetime = Field(description="datetime of the creation.")
    updated: datetime.datetime | None = Field(
        description="datetime of the last update.", default=None
    )


# Proof
# ProofBase > ProofCreate > ProofFull > ProofFullWithRelations
# ProofBase > ProofUpdate
# ------------------------------------------------------------------------------
class ProofBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, arbitrary_types_allowed=True, extra="forbid"
    )

    type: ProofTypeEnum | None = None
    currency: CurrencyEnum | None = Field(
        description="currency of the price, as a string. "
        "The currency must be a valid currency code. "
        "See https://en.wikipedia.org/wiki/ISO_4217 for a list of valid currency codes.",
        examples=["EUR", "USD"],
    )
    date: datetime.date | None = Field(
        description="date of the proof.", examples=["2024-01-01"]
    )


class ProofCreate(ProofBase):
    # file_path is str | null because we can mask the file path in the response
    # if the proof is not public
    file_path: str | None
    mimetype: str
    location_osm_id: int | None = Field(
        gt=0,
        description="ID of the location in OpenStreetMap: the store where the product was bought.",
        examples=[1234567890],
    )
    location_osm_type: LocationOSMEnum | None = Field(
        description="type of the OpenStreetMap location object. Stores can be represented as nodes, "
        "ways or relations in OpenStreetMap. It is necessary to be able to fetch the correct "
        "information about the store using the ID.",
        examples=["NODE", "WAY", "RELATION"],
    )


@partial_model
class ProofUpdate(ProofBase):
    pass


class ProofFull(ProofCreate):
    id: int
    price_count: int = Field(
        description="number of prices for this proof.", examples=[15], default=0
    )
    location_id: int | None
    owner: str
    # source: str | None = Field(
    #     description="Source (App name)",
    #     examples=["web app", "mobile app"],
    #     default=None,
    # )
    created: datetime.datetime = Field(description="datetime of the creation.")
    updated: datetime.datetime | None = Field(
        description="datetime of the last update.", default=None
    )


class ProofFullWithRelations(ProofFull):
    location: LocationFull | None


# Price
# PriceBase > PriceBaseWithValidation & PriceCreate > PriceCreateWithValidation
# PriceBase > PriceBaseWithValidation > PriceUpdateWithValidation
# PriceBase > PriceCreate > PriceFull > PriceFullWithRelations
# ------------------------------------------------------------------------------
class PriceBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, arbitrary_types_allowed=True, extra="forbid"
    )

    price: float = Field(
        gt=0,
        description="price of the product, without its currency, taxes included.",
        examples=[1.99],
    )
    price_is_discounted: bool = Field(
        default=False,
        description="true if the price is discounted.",
        examples=[True],
    )
    price_without_discount: float | None = Field(
        default=None,
        description="price of the product without discount, without its currency, taxes included. "
        "If the product is not discounted, this field must be null.",
        examples=[2.99],
    )
    price_per: PricePerEnum | None = Field(
        default=PricePerEnum.KILOGRAM,
        description="""if the price is about a barcode-less product
        (if `category_tag` is provided), this field must be set to `KILOGRAM`
        or `UNIT` (KILOGRAM by default).
        This field is set to null and ignored if `product_code` is provided.
        """,
        examples=["KILOGRAM", "UNIT"],
    )
    currency: CurrencyEnum = Field(
        description="currency of the price, as a string. "
        "The currency must be a valid currency code. "
        "See https://en.wikipedia.org/wiki/ISO_4217 for a list of valid currency codes.",
        examples=["EUR", "USD"],
    )
    date: datetime.date = Field(
        description="date when the product was bought.", examples=["2024-01-01"]
    )


class PriceBaseWithValidation(PriceBase):
    """A version of `PriceBase` with validations.
    These validations are not done in the `PriceFull` model
    because they are time-consuming and only necessary when creating or
    updating a price from the API.
    """

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


class PriceCreate(PriceBase):
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
        examples=[["en:organic"], ["fr:ab-agriculture-biologique", "en:fair-trade"]],
    )
    origins_tags: list[str] | None = Field(
        default=None,
        description="""origins of the product, only for products without barcode.

        This field is a list as some products may be a mix of several origins,
        but most products have only one origin.

        The origins must be valid origins in the Open Food Facts taxonomy.
        If one of the origins is not valid, the price will be rejected.""",
        examples=[["en:france"], ["en:california"]],
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
        examples=["NODE", "WAY", "RELATION"],
    )
    proof_id: int | None = Field(
        default=None,
        description="ID of the proof, if any. The proof is a file (receipt or price tag image) "
        "uploaded by the user to prove the price of the product. "
        "The proof must be uploaded before the price, and the authenticated user must be the "
        "owner of the proof.",
        examples=[15],
    )


class PriceCreateWithValidation(PriceBaseWithValidation, PriceCreate):
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


@partial_model
class PriceUpdateWithValidation(PriceBaseWithValidation):
    pass


class PriceFull(PriceCreate):
    id: int
    product_id: int | None
    location_id: int | None
    owner: str
    # source: str | None = Field(
    #     description="Source (App name)",
    #     examples=["web app", "mobile app"],
    #     default=None,
    # )
    created: datetime.datetime = Field(description="datetime of the creation.")
    updated: datetime.datetime | None = Field(
        description="datetime of the last update.", default=None
    )


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
    date__year: Optional[str] | None = None  # custom (see crud.py)
    date__month: Optional[str] | None = None  # custom (see crud.py)
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
    location_osm_id: Optional[int] | None = None
    location_osm_type: Optional[LocationOSMEnum] | None = None
    location_id: Optional[int] | None = None
    date: Optional[str] | None = None
    currency: Optional[str] | None = None
    date__gt: Optional[str] | None = None
    date__gte: Optional[str] | None = None
    date__lt: Optional[str] | None = None
    date__lte: Optional[str] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Proof


class ProductFilter(Filter):
    code: Optional[str] | None = None
    source: Optional[Flavor] | None = None
    product_name__like: Optional[str] | None = None
    categories_tags__contains: Optional[str] | None = None  # custom (see crud.py)
    labels_tags__contains: Optional[str] | None = None  # custom (see crud.py)
    brands__like: Optional[str] | None = None
    nutriscore_grade: Optional[str] | None = None
    ecoscore_grade: Optional[str] | None = None
    nova_group: Optional[int] | None = None
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
