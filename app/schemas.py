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
from app.models import Price, Product


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    code: str = Field(
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["8001505005707"],
    )


class ProductBase(ProductCreate):
    id: int
    source: Flavor | None = Field(
        description="source of data, either `off` (Open Food Facts), "
        "`obf` (Open Beauty Facts), `opff` (Open Pet Food Facts) or `obf` (Open Beauty Facts)"
    )
    product_name: str | None = Field(
        description="name of the product.", examples=["Nocciolata"]
    )
    product_quantity: int | None = Field(
        description="quantity of the product, normalized in g or mL (depending on the product).",
        examples=[700],
    )
    brands: str | None = Field(
        description="brand(s) of the product.",
        examples=["Rigoni di Asiago", "Lindt"],
    )
    image_url: AnyHttpUrl | None = Field(
        description="URL of the product image.",
        examples=[
            "https://images.openfoodfacts.org/images/products/800/150/500/5707/front_fr.161.400.jpg"
        ],
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


class LocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    osm_id: int = Field(gt=0)
    osm_type: LocationOSMEnum


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
    def labels_tags_is_valid(cls, v: list[str] | None):
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
    def origins_tags_is_valid(cls, v: list[str] | None):
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
    def category_tag_is_valid(cls, v: str | None):
        if v is not None:
            v = v.lower()
            category_taxonomy = get_taxonomy("category")
            if v not in category_taxonomy:
                raise ValueError(
                    f"Invalid category tag: category '{v}' does not exist in the taxonomy"
                )
        return v

    @model_validator(mode="after")
    def product_code_and_category_tag_are_exclusive(self):
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
    def set_price_per_to_null_if_barcode(self):
        """Validator that sets `price_per` to null if `product_code` is set."""
        if self.product_code is not None:
            self.price_per = None
        return self

    @model_validator(mode="after")
    def check_price_without_discout(self):
        """Check that `price_without_discount` is greater than `price`."""
        if self.price_without_discount is not None:
            if self.price_without_discount <= self.price:
                raise ValueError(
                    "`price_without_discount` must be greater than `price`"
                )
        return self


class PriceBase(PriceCreate):
    product_id: int | None
    location_id: int | None
    owner: str
    created: datetime.datetime


# class ProofCreate(BaseModel):
#     file: UploadFile
#     type: ProofTypeEnum


class ProofBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    # file_path is str | null because we can mask the file path in the response
    # if the proof is not public
    file_path: str | None
    mimetype: str
    type: ProofTypeEnum | None = None
    owner: str
    created: datetime.datetime
    is_public: Annotated[
        bool,
        Field(
            default=True,
            description="if true, the proof is public and is included in the API response. "
            "Set false if only if the proof contains personal information.",
        ),
    ]


class PriceFull(PriceBase):
    product: ProductBase | None
    proof: ProofBase | None
    location: LocationBase | None


class PriceFilter(Filter):
    product_code: Optional[str] | None = None
    product_id: Optional[int] | None = None
    product_id__isnull: Optional[bool] | None = None
    category_tag: Optional[str] | None = None
    labels_tags__like: Optional[str] | None = None
    origins_tags__like: Optional[str] | None = None
    location_osm_id: Optional[int] | None = None
    location_osm_type: Optional[LocationOSMEnum] | None = None
    location_id: Optional[int] | None = None
    price: Optional[int] | None = None
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
    owner: Optional[str] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Price


class ProductFilter(Filter):
    code: Optional[str] | None = None
    source: Optional[Flavor] | None = None
    product_name__like: Optional[str] | None = None
    brands__like: Optional[str] | None = None
    unique_scans_n__gte: Optional[int] | None = None
    price_count: Optional[int] | None = None
    price_count__gte: Optional[int] | None = None
    price_count__lte: Optional[int] | None = None

    order_by: Optional[list[str]] | None = None

    class Constants(Filter.Constants):
        model = Product
